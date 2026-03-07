# Lab 09: Kubernetes Operator Patterns

**Time:** 60 minutes | **Level:** Architect | **Docker:** `golang:1.22-alpine`

## Overview

Kubernetes operator concepts in Go: Reconciler interface, controller-runtime patterns, CRD definition (runtime.Object), reconcile loop pattern, informer/lister pattern (with fake client for testing), and operator-sdk concepts.

---

## Step 1: Reconciler Interface

```go
package controller

import (
	"context"
	"fmt"
	"time"

	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
)

// Reconciler: the core interface of every operator
type Reconciler interface {
	Reconcile(ctx context.Context, req reconcile.Request) (reconcile.Result, error)
}

// reconcile.Request: identifies the object to reconcile
// reconcile.Result: tells the controller when to requeue
//   Result{}: Don't requeue
//   Result{Requeue: true}: Requeue immediately
//   Result{RequeueAfter: 30*time.Second}: Requeue after 30s

// The controller-runtime calling loop:
//   1. Watch resources for changes
//   2. Enqueue NamespacedName into work queue
//   3. Call Reconcile(req) for each item
//   4. Handle Result.RequeueAfter for periodic reconciliation
//   5. Retry on error (with exponential backoff)
```

---

## Step 2: Custom Resource Definition (CRD)

```go
package v1alpha1

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
)

// WebApp is a custom Kubernetes resource
// CRD YAML defines: group, version, kind, schema

// Spec: desired state (what we want)
type WebAppSpec struct {
	Replicas  int32  `json:"replicas"`
	Image     string `json:"image"`
	Port      int32  `json:"port"`
	EnableTLS bool   `json:"enableTLS,omitempty"`
}

// Status: current state (what we have)
type WebAppStatus struct {
	AvailableReplicas int32      `json:"availableReplicas"`
	Phase             string     `json:"phase"` // Pending, Running, Failed
	Conditions        []metav1.Condition `json:"conditions,omitempty"`
	LastReconciled    *metav1.Time `json:"lastReconciled,omitempty"`
}

// WebApp: the CRD type
type WebApp struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`
	Spec   WebAppSpec   `json:"spec,omitempty"`
	Status WebAppStatus `json:"status,omitempty"`
}

// Implement runtime.Object
func (w *WebApp) DeepCopyObject() runtime.Object {
	copy := *w
	return &copy
}

// WebAppList
type WebAppList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items []WebApp  `json:"items"`
}

func (w *WebAppList) DeepCopyObject() runtime.Object {
	copy := *w
	return &copy
}
```

---

## Step 3: Reconcile Loop Pattern

```go
package controller

import (
	"context"
	"fmt"

	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
)

type WebAppReconciler struct {
	client.Client
}

func (r *WebAppReconciler) Reconcile(ctx context.Context, req reconcile.Request) (reconcile.Result, error) {
	// Step 1: Fetch the custom resource
	app := &WebApp{}
	if err := r.Get(ctx, req.NamespacedName, app); err != nil {
		if errors.IsNotFound(err) {
			// Object deleted — nothing to do
			return reconcile.Result{}, nil
		}
		return reconcile.Result{}, fmt.Errorf("get webapp: %w", err)
	}

	// Step 2: Check deletion (finalizer pattern)
	if !app.DeletionTimestamp.IsZero() {
		return r.handleDeletion(ctx, app)
	}

	// Step 3: Add finalizer if missing
	if err := r.ensureFinalizer(ctx, app); err != nil {
		return reconcile.Result{}, err
	}

	// Step 4: Reconcile desired state
	if err := r.reconcileDeployment(ctx, app); err != nil {
		app.Status.Phase = "Failed"
		r.Status().Update(ctx, app)
		return reconcile.Result{}, err
	}

	if err := r.reconcileService(ctx, app); err != nil {
		return reconcile.Result{}, err
	}

	// Step 5: Update status
	app.Status.Phase = "Running"
	r.Status().Update(ctx, app)

	// Step 6: Requeue periodically to drift-correct
	return reconcile.Result{RequeueAfter: 30 * time.Second}, nil
}

func (r *WebAppReconciler) reconcileDeployment(ctx context.Context, app *WebApp) error {
	deployment := &appsv1.Deployment{}
	err := r.Get(ctx, client.ObjectKeyFromObject(app), deployment)

	if errors.IsNotFound(err) {
		// Create deployment
		desired := r.buildDeployment(app)
		return r.Create(ctx, desired)
	}
	if err != nil {
		return err
	}

	// Update if spec changed
	if *deployment.Spec.Replicas != app.Spec.Replicas {
		deployment.Spec.Replicas = &app.Spec.Replicas
		return r.Update(ctx, deployment)
	}
	return nil
}
```

---

## Step 4: Fake Client for Testing

```go
package controller_test

import (
	"context"
	"testing"

	"sigs.k8s.io/controller-runtime/pkg/client/fake"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
)

func TestWebAppReconciler(t *testing.T) {
	// Build fake client with existing objects
	app := &WebApp{
		ObjectMeta: metav1.ObjectMeta{Name: "my-app", Namespace: "default"},
		Spec: WebAppSpec{Replicas: 3, Image: "nginx:latest", Port: 8080},
	}

	fakeClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithObjects(app).
		WithStatusSubresource(app).
		Build()

	reconciler := &WebAppReconciler{Client: fakeClient}

	// Test reconcile
	result, err := reconciler.Reconcile(context.Background(), reconcile.Request{
		NamespacedName: types.NamespacedName{Name: "my-app", Namespace: "default"},
	})

	if err != nil {
		t.Fatalf("Reconcile failed: %v", err)
	}

	// Verify deployment was created
	deployment := &appsv1.Deployment{}
	if err := fakeClient.Get(context.Background(),
		types.NamespacedName{Name: "my-app", Namespace: "default"},
		deployment); err != nil {
		t.Fatalf("Deployment not created: %v", err)
	}

	if *deployment.Spec.Replicas != 3 {
		t.Errorf("Expected 3 replicas, got %d", *deployment.Spec.Replicas)
	}

	_ = result
}
```

---

## Step 5: Informer and Lister Pattern

```go
package cache

import (
	"k8s.io/client-go/informers"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/tools/cache"
)

// Informer: watches k8s API, caches locally, calls event handlers
func SetupInformers(client *kubernetes.Clientset) {
	factory := informers.NewSharedInformerFactory(client, 30*time.Second)

	podInformer := factory.Core().V1().Pods().Informer()
	podLister   := factory.Core().V1().Pods().Lister()

	// Register event handlers
	podInformer.AddEventHandler(cache.ResourceEventHandlerFuncs{
		AddFunc: func(obj interface{}) {
			pod := obj.(*corev1.Pod)
			fmt.Printf("Pod added: %s/%s\n", pod.Namespace, pod.Name)
		},
		UpdateFunc: func(old, new interface{}) {
			// Only process if resource version changed
			oldPod := old.(*corev1.Pod)
			newPod := new.(*corev1.Pod)
			if oldPod.ResourceVersion == newPod.ResourceVersion {
				return  // Resync, not real change
			}
			fmt.Printf("Pod updated: %s/%s\n", newPod.Namespace, newPod.Name)
		},
		DeleteFunc: func(obj interface{}) {
			pod := obj.(*corev1.Pod)
			fmt.Printf("Pod deleted: %s/%s\n", pod.Namespace, pod.Name)
		},
	})

	// Start informers
	stopCh := make(chan struct{})
	factory.Start(stopCh)
	factory.WaitForCacheSync(stopCh)

	// List from local cache (no API call)
	pods, _ := podLister.Pods("default").List(labels.Everything())
	fmt.Printf("Cached pods in default: %d\n", len(pods))
}
```

---

## Step 6: Controller Setup with controller-runtime

```go
package main

import (
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/log/zap"
)

func main() {
	ctrl.SetLogger(zap.New())

	mgr, err := ctrl.NewManager(ctrl.GetConfigOrDie(), ctrl.Options{
		Scheme: scheme,
		// Metrics endpoint
		MetricsBindAddress: ":8080",
		// Health check
		HealthProbeBindAddress: ":8081",
		// Leader election: only one pod reconciles at a time
		LeaderElection:         true,
		LeaderElectionID:       "webapp-operator.io",
	})
	if err != nil {
		panic(err)
	}

	// Register our reconciler
	if err := (&WebAppReconciler{Client: mgr.GetClient()}).SetupWithManager(mgr); err != nil {
		panic(err)
	}

	// Health endpoints
	mgr.AddHealthzCheck("healthz", healthz.Ping)
	mgr.AddReadyzCheck("readyz", healthz.Ping)

	if err := mgr.Start(ctrl.SetupSignalHandler()); err != nil {
		panic(err)
	}
}

// SetupWithManager: define what resources to watch
func (r *WebAppReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&WebApp{}).              // Primary resource (triggers reconcile)
		Owns(&appsv1.Deployment{}).  // Reconcile when owned deployment changes
		Owns(&corev1.Service{}).     // Reconcile when owned service changes
		Complete(r)
}
```

---

## Step 7: Finalizer Pattern

```go
func (r *WebAppReconciler) ensureFinalizer(ctx context.Context, app *WebApp) error {
	if controllerutil.ContainsFinalizer(app, "webapp.io/cleanup") {
		return nil
	}
	controllerutil.AddFinalizer(app, "webapp.io/cleanup")
	return r.Update(ctx, app)
}

func (r *WebAppReconciler) handleDeletion(ctx context.Context, app *WebApp) (reconcile.Result, error) {
	if !controllerutil.ContainsFinalizer(app, "webapp.io/cleanup") {
		return reconcile.Result{}, nil
	}

	// Cleanup: remove external resources not managed by k8s ownership
	if err := r.cleanupExternalResources(ctx, app); err != nil {
		return reconcile.Result{}, err
	}

	// Remove finalizer to allow deletion to proceed
	controllerutil.RemoveFinalizer(app, "webapp.io/cleanup")
	return reconcile.Result{}, r.Update(ctx, app)
}
```

---

## Step 8: Capstone — Reconciler Demo (stdlib only)

```bash
docker run --rm golang:1.22-alpine sh -c "cat > /tmp/main.go << 'GOEOF'
package main
import (\"context\"; \"fmt\"; \"time\")

type Request struct{ Namespace, Name string }
type Result struct{ RequeueAfter time.Duration }

type Reconciler interface{ Reconcile(context.Context, Request) (Result, error) }

type Deployment struct { Namespace, Name string; Replicas int32; ReadyReplicas int32 }
type FakeClient struct{ deployments map[string]*Deployment }
func (c *FakeClient) Get(ns, name string) (*Deployment, bool) { d, ok := c.deployments[ns+\"/\"+name]; return d, ok }
func (c *FakeClient) UpdateStatus(d *Deployment) {
  d.ReadyReplicas = d.Replicas
  fmt.Printf(\"  [fake-client] Updated status for %s/%s: ready=%d\\n\", d.Namespace, d.Name, d.ReadyReplicas)
}

type AppReconciler struct{ client *FakeClient }
func (r *AppReconciler) Reconcile(ctx context.Context, req Request) (Result, error) {
  d, ok := r.client.Get(req.Namespace, req.Name)
  if !ok { fmt.Printf(\"  [reconcile] %s/%s not found, skipping\\n\", req.Namespace, req.Name); return Result{}, nil }
  fmt.Printf(\"  [reconcile] Processing %s/%s (replicas=%d, ready=%d)\\n\", req.Namespace, req.Name, d.Replicas, d.ReadyReplicas)
  if d.ReadyReplicas != d.Replicas {
    fmt.Printf(\"  [reconcile] Scaling up from %d to %d\\n\", d.ReadyReplicas, d.Replicas)
    r.client.UpdateStatus(d)
  } else { fmt.Printf(\"  [reconcile] %s/%s is healthy\\n\", req.Namespace, req.Name) }
  return Result{}, nil
}

func main() {
  client := &FakeClient{deployments: map[string]*Deployment{\"default/my-app\": {\"default\",\"my-app\",3,0}}}
  rec := &AppReconciler{client}
  fmt.Println(\"=== Kubernetes Reconciler Demo ===\")
  req := Request{\"default\", \"my-app\"}
  r1, e1 := rec.Reconcile(context.Background(), req)
  fmt.Printf(\"Result: requeue=%v, err=%v\\n\", r1.RequeueAfter, e1)
  r2, e2 := rec.Reconcile(context.Background(), req)
  fmt.Printf(\"Result2: requeue=%v, err=%v\\n\", r2.RequeueAfter, e2)
  req.Name = \"not-found\"
  r3, e3 := rec.Reconcile(context.Background(), req)
  fmt.Printf(\"NotFound: requeue=%v, err=%v\\n\", r3.RequeueAfter, e3)
}
GOEOF
cd /tmp && go run main.go"
```

📸 **Verified Output:**
```
=== Kubernetes Reconciler Demo ===
  [reconcile] Processing default/my-app (replicas=3, ready=0)
  [reconcile] Scaling up from 0 to 3
  [fake-client] Updated status for default/my-app: ready=3
Result: requeue=0s, err=<nil>
  [reconcile] Processing default/my-app (replicas=3, ready=3)
  [reconcile] default/my-app is healthy
Result2: requeue=0s, err=<nil>
  [reconcile] default/not-found not found, skipping
NotFound: requeue=0s, err=<nil>
```

---

## Summary

| Concept | controller-runtime API | Notes |
|---------|----------------------|-------|
| Reconciler | `Reconcile(ctx, req) (Result, error)` | Core reconcile loop |
| CRD | `runtime.Object` + `DeepCopyObject` | Typed k8s resource |
| Watch | `ctrl.NewControllerManagedBy.For()` | Trigger events |
| Owns | `.Owns(&Deployment{})` | Cascade reconcile |
| Fake client | `fake.NewClientBuilder()` | Unit testing |
| Informer | `SharedInformerFactory` | Local cache |
| Finalizer | `controllerutil.AddFinalizer` | Cleanup on delete |
| Leader election | `LeaderElection: true` | One active reconciler |
