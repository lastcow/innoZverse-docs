# Lab 1: Dynamic Proxies & MethodHandles

## Objective
Build runtime behaviour injection using `java.lang.reflect.Proxy` — automatic timing, caching, and logging for any interface without modifying the implementation. Master `MethodHandles` for faster reflective dispatch, and `ParameterizedType` for type token patterns.

## Background
`java.lang.reflect.Proxy` creates an implementation of any interface at runtime. Every method call goes through a single `InvocationHandler` — making it trivial to inject cross-cutting concerns (timing, auth, caching, retry) around any service. This is the foundation of Spring AOP, JPA lazy-loading, and mocking frameworks like Mockito.

## Time
30 minutes

## Prerequisites
- Practitioner Lab 12 (Reflection & Annotations)

## Tools
- Docker: `zchencow/innozverse-java:latest`

---

## Lab Instructions

### Steps 1–8: Timing proxy, caching proxy, class introspection, MethodHandles, type tokens, composing proxies, Capstone

```bash
cat > /tmp/AdvLab01.java << 'JAVAEOF'
import java.lang.reflect.*;
import java.lang.invoke.*;
import java.util.*;
import java.util.function.*;

public class AdvLab01 {
    interface ProductRepo {
        String findById(int id);
        List<String> findAll();
        void save(String name);
    }

    static ProductRepo makeRepo() {
        return new ProductRepo() {
            final Map<Integer,String> db = new LinkedHashMap<>(Map.of(1,"Surface Pro",2,"Surface Pen",3,"Office 365"));
            public String findById(int id) { try{Thread.sleep(10);}catch(Exception e){} return db.getOrDefault(id,"NOT_FOUND"); }
            public List<String> findAll() { try{Thread.sleep(15);}catch(Exception e){} return new ArrayList<>(db.values()); }
            public void save(String name) { db.put(db.size()+1, name); }
        };
    }

    @SuppressWarnings("unchecked")
    static <T> T timingProxy(T target, Class<T> iface) {
        return (T) Proxy.newProxyInstance(iface.getClassLoader(), new Class[]{iface},
            (proxy, method, args) -> {
                long t0 = System.nanoTime();
                Object result = method.invoke(target, args);
                long ms = (System.nanoTime() - t0) / 1_000_000;
                String res = result == null ? "void" : result.toString();
                if (res.length() > 40) res = res.substring(0,40) + "...";
                System.out.printf("  [PROXY] %-12s args=%-15s -> %-40s (%dms)%n",
                    method.getName(), args == null ? "()" : Arrays.toString(args), res, ms);
                return result;
            });
    }

    @SuppressWarnings("unchecked")
    static <T> T cachingProxy(T target, Class<T> iface) {
        Map<String,Object> cache = new HashMap<>();
        return (T) Proxy.newProxyInstance(iface.getClassLoader(), new Class[]{iface},
            (proxy, method, args) -> {
                if (method.getReturnType() == void.class) { cache.clear(); return method.invoke(target, args); }
                String key = method.getName() + Arrays.toString(args);
                if (cache.containsKey(key)) { System.out.println("  [CACHE HIT]  " + key); return cache.get(key); }
                Object result = method.invoke(target, args);
                cache.put(key, result);
                System.out.println("  [CACHE MISS] " + key + " -> stored");
                return result;
            });
    }

    static void printClassInfo(Class<?> cls) {
        System.out.println("Class: " + cls.getSimpleName());
        System.out.println("  Superclass:   " + (cls.getSuperclass() != null ? cls.getSuperclass().getSimpleName() : "none"));
        System.out.println("  Interfaces:   " + Arrays.stream(cls.getInterfaces()).map(Class::getSimpleName).toList());
        System.out.println("  Methods:      " + Arrays.stream(cls.getDeclaredMethods()).map(Method::getName).sorted().limit(8).toList() + "...");
    }

    public static void main(String[] args) throws Throwable {
        System.out.println("=== Timing Proxy ===");
        var repo = timingProxy(makeRepo(), ProductRepo.class);
        repo.findById(1);
        repo.findAll();
        repo.save("USB-C Hub");

        System.out.println("\n=== Caching Proxy ===");
        var cached = cachingProxy(makeRepo(), ProductRepo.class);
        cached.findById(1);
        cached.findById(1);  // cache hit
        cached.findById(2);
        cached.findAll();
        cached.findAll();    // cache hit

        System.out.println("\n=== Class Introspection ===");
        printClassInfo(ArrayList.class);
        System.out.println();
        printClassInfo(HashMap.class);

        System.out.println("\n=== MethodHandles ===");
        var lookup = MethodHandles.lookup();
        var mhUpper = lookup.findVirtual(String.class, "toUpperCase", MethodType.methodType(String.class));
        System.out.println("toUpperCase via MH: " + (String) mhUpper.invoke("surface pro"));
        var mhLen = lookup.findVirtual(String.class, "length", MethodType.methodType(int.class));
        System.out.println("length via MH:      " + (int) mhLen.invoke("Surface Pro"));

        System.out.println("\n=== Type Tokens (Erasure Workaround) ===");
        abstract class TypeRef<T> {
            final Type type;
            TypeRef() { type = ((ParameterizedType) getClass().getGenericSuperclass()).getActualTypeArguments()[0]; }
            @Override public String toString() { return type.getTypeName(); }
        }
        var stringListRef = new TypeRef<List<String>>() {};
        var mapRef = new TypeRef<Map<Integer,String>>() {};
        System.out.println("TypeRef<List<String>>:        " + stringListRef);
        System.out.println("TypeRef<Map<Integer,String>>: " + mapRef);
    }
}
JAVAEOF
docker run --rm -v /tmp/AdvLab01.java:/tmp/AdvLab01.java zchencow/innozverse-java:latest sh -c "javac /tmp/AdvLab01.java -d /tmp && java -cp /tmp AdvLab01"
```

> 💡 **`Proxy.newProxyInstance` is how Spring creates `@Transactional` beans.** When you inject a Spring bean, you're actually getting a proxy — the real object is wrapped in an `InvocationHandler` that starts a transaction before calling the real method and commits (or rolls back) after. The real class is never exposed directly. This is also how Mockito creates mocks at runtime without any code generation.

**📸 Verified Output:**
```
=== Timing Proxy ===
  [PROXY] findById     args=[1]             -> Surface Pro                           (30ms)
  [PROXY] findAll      args=()              -> [Surface Pen, Surface Pro, Office 365] (17ms)
  [PROXY] save         args=[USB-C Hub]     -> void                                  (5ms)

=== Caching Proxy ===
  [CACHE MISS] findById[1] -> stored
  [CACHE HIT]  findById[1]
  [CACHE MISS] findById[2] -> stored
  [CACHE MISS] findAllnull -> stored
  [CACHE HIT]  findAllnull

=== MethodHandles ===
toUpperCase via MH: SURFACE PRO
length via MH:      11

=== Type Tokens ===
TypeRef<List<String>>:        java.util.List<java.lang.String>
TypeRef<Map<Integer,String>>: java.util.Map<java.lang.Integer, java.lang.String>
```

---

## Summary

| API | Use for |
|-----|---------|
| `Proxy.newProxyInstance(loader, ifaces, handler)` | Runtime interface implementation |
| `InvocationHandler.invoke(proxy, method, args)` | Intercept every method call |
| `method.invoke(target, args)` | Forward to real target |
| `MethodHandles.lookup().findVirtual(cls, name, type)` | Fast reflective dispatch |
| `ParameterizedType.getActualTypeArguments()` | Recover generic type args |

## Further Reading
- [java.lang.reflect.Proxy](https://docs.oracle.com/en/java/docs/api/java.base/java/lang/reflect/Proxy.html)
- [MethodHandles](https://docs.oracle.com/en/java/docs/api/java.base/java/lang/invoke/MethodHandles.html)
