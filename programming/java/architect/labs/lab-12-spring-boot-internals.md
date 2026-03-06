# Lab 12: Spring Boot Internals — Manual DI Container

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-java:latest bash`

---

## Overview

Understand Spring Boot's magic by building it from scratch: a manual DI container using custom annotations and reflection, property binding, condition evaluation, and application context lifecycle — all without any Spring dependency.

---

## Step 1: Spring Boot Internals Overview

```
Spring Boot startup sequence:
  1. SpringApplication.run()
     ├── Detect application type (Servlet/Reactive/None)
     ├── Load ApplicationContext initializers
     ├── Load ApplicationListeners
     └── Create ApplicationContext
  2. Context refresh:
     ├── BeanDefinition scanning (@Component, @Service, @Repository)
     ├── BeanFactory post-processing (@Configuration + @Bean)
     ├── Condition evaluation (@ConditionalOnProperty, @ConditionalOnClass)
     ├── Bean instantiation (constructor injection)
     ├── Dependency injection (@Autowired, @Value)
     └── Lifecycle callbacks (@PostConstruct, ApplicationRunner)
  3. Embed Tomcat/Jetty/Undertow

What we'll build:
  @Component → register bean
  @Inject    → field injection
  @Value     → property binding
  Condition  → conditional bean creation
  BeanFactory lifecycle
```

---

## Step 2: Custom Annotations

```java
import java.lang.annotation.*;

// @Component: marks class as a managed bean
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.TYPE)
@interface Component {
    String value() default "";
}

// @Inject: marks field for dependency injection
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.FIELD)
@interface Inject {}

// @Value: bind property value
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.FIELD)
@interface Value {
    String value(); // e.g., "${db.url}" or "${server.port:8080}"
}

// @PostConstruct: lifecycle callback
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
@interface PostConstruct {}

// @ConditionalOnProperty: conditional bean creation
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.TYPE)
@interface ConditionalOnProperty {
    String name();
    String havingValue() default "true";
}
```

---

## Step 3: BeanDefinition and BeanFactory

```java
import java.lang.reflect.*;
import java.util.*;

class BeanDefinition {
    final Class<?> beanClass;
    final String beanName;
    final boolean isSingleton;
    Object instance; // null until created
    
    BeanDefinition(Class<?> cls) {
        this.beanClass = cls;
        Component ann = cls.getAnnotation(Component.class);
        String name = ann != null && !ann.value().isEmpty()
            ? ann.value() : lowerCamelCase(cls.getSimpleName());
        this.beanName = name;
        this.isSingleton = true; // default Spring scope
    }
    
    private static String lowerCamelCase(String name) {
        return Character.toLowerCase(name.charAt(0)) + name.substring(1);
    }
}

class SimpleBeanFactory {
    private final Map<String, BeanDefinition> definitions = new LinkedHashMap<>();
    private final Map<Class<?>, String> typeIndex = new HashMap<>();
    private final Properties properties;
    
    SimpleBeanFactory(Properties properties) { this.properties = properties; }
    
    void register(Class<?>... classes) throws Exception {
        for (Class<?> cls : classes) {
            // Check conditional
            ConditionalOnProperty cond = cls.getAnnotation(ConditionalOnProperty.class);
            if (cond != null) {
                String actual = properties.getProperty(cond.name(), "false");
                if (!actual.equals(cond.havingValue())) {
                    System.out.println("Skip (condition false): " + cls.getSimpleName());
                    continue;
                }
            }
            BeanDefinition def = new BeanDefinition(cls);
            definitions.put(def.beanName, def);
            typeIndex.put(cls, def.beanName);
        }
    }
    
    void refresh() throws Exception {
        // Phase 1: Instantiate all beans
        for (BeanDefinition def : definitions.values()) {
            if (def.instance == null) {
                def.instance = def.beanClass.getDeclaredConstructor().newInstance();
                System.out.println("Instantiated: " + def.beanName);
            }
        }
        
        // Phase 2: Inject @Inject and @Value fields
        for (BeanDefinition def : definitions.values()) {
            for (Field field : def.beanClass.getDeclaredFields()) {
                field.setAccessible(true);
                
                if (field.isAnnotationPresent(Inject.class)) {
                    // Find bean by type
                    String depName = typeIndex.get(field.getType());
                    if (depName == null) throw new RuntimeException(
                        "No bean found for type: " + field.getType().getSimpleName());
                    BeanDefinition dep = definitions.get(depName);
                    field.set(def.instance, dep.instance);
                    System.out.println("Injected: " + def.beanName + "." + field.getName() + " → " + depName);
                }
                
                if (field.isAnnotationPresent(Value.class)) {
                    String expr = field.getAnnotation(Value.class).value();
                    String val = resolveValue(expr);
                    field.set(def.instance, convertValue(val, field.getType()));
                }
            }
        }
        
        // Phase 3: @PostConstruct callbacks
        for (BeanDefinition def : definitions.values()) {
            for (Method m : def.beanClass.getDeclaredMethods()) {
                if (m.isAnnotationPresent(PostConstruct.class)) {
                    m.setAccessible(true);
                    m.invoke(def.instance);
                }
            }
        }
    }
    
    String resolveValue(String expr) {
        if (expr.startsWith("${") && expr.endsWith("}")) {
            String key = expr.substring(2, expr.length() - 1);
            String[] parts = key.split(":", 2);
            return properties.getProperty(parts[0], parts.length > 1 ? parts[1] : null);
        }
        return expr;
    }
    
    Object convertValue(String val, Class<?> type) {
        if (type == int.class || type == Integer.class) return Integer.parseInt(val);
        if (type == boolean.class) return Boolean.parseBoolean(val);
        return val;
    }
    
    @SuppressWarnings("unchecked")
    <T> T getBean(String name) {
        BeanDefinition def = definitions.get(name);
        if (def == null) throw new RuntimeException("No bean: " + name);
        return (T) def.instance;
    }
    
    @SuppressWarnings("unchecked")
    <T> T getBean(Class<T> type) {
        String name = typeIndex.get(type);
        if (name == null) throw new RuntimeException("No bean of type: " + type.getSimpleName());
        return (T) definitions.get(name).instance;
    }
    
    Set<String> getBeanNames() { return definitions.keySet(); }
}
```

---

## Step 4: Bean Classes

```java
@Component("dataSource")
class DataSource {
    @Value("${db.url:jdbc:sqlite:app.db}")
    String url;
    
    @Value("${db.pool.size:10}")
    int poolSize;
    
    @PostConstruct
    void init() {
        System.out.println("DataSource initialized: " + url + " (pool=" + poolSize + ")");
    }
    
    public String getConnection() { return url; }
}

@Component("userRepository")
class UserRepository {
    @Inject DataSource dataSource;
    
    public String findUser(int id) {
        return "User[" + id + "] via " + dataSource.getConnection();
    }
}

@Component("userService")
class UserService {
    @Inject UserRepository repo;
    
    @Value("${service.name:UserService}")
    String serviceName;
    
    public String getUser(int id) {
        return serviceName + " → " + repo.findUser(id);
    }
}

// Conditional bean — only created if feature.cache=true
@Component("cacheService")
@ConditionalOnProperty(name = "feature.cache", havingValue = "true")
class CacheService {
    public String get(String key) { return "cached:" + key; }
}
```

---

## Step 5: Property Binding

```java
import java.util.*;
import java.lang.reflect.*;
import java.io.*;

public class PropertyBindingDemo {
    // Bind Properties to a typed config object via reflection
    static <T> T bind(Properties props, String prefix, Class<T> configClass) throws Exception {
        T config = configClass.getDeclaredConstructor().newInstance();
        for (Field field : configClass.getDeclaredFields()) {
            String key = prefix + "." + camelToKebab(field.getName());
            String value = props.getProperty(key);
            if (value != null) {
                field.setAccessible(true);
                field.set(config, convertValue(value, field.getType()));
            }
        }
        return config;
    }
    
    static String camelToKebab(String camel) {
        return camel.replaceAll("([A-Z])", "-$1").toLowerCase();
    }
    
    static Object convertValue(String val, Class<?> type) {
        if (type == int.class || type == Integer.class) return Integer.parseInt(val);
        if (type == long.class || type == Long.class) return Long.parseLong(val);
        if (type == boolean.class) return Boolean.parseBoolean(val);
        return val;
    }
    
    static class ServerConfig {
        int port;
        String host;
        int maxConnections;
        boolean ssl;
    }
    
    public static void main(String[] args) throws Exception {
        Properties props = new Properties();
        props.setProperty("server.port", "8080");
        props.setProperty("server.host", "localhost");
        props.setProperty("server.max-connections", "200");
        props.setProperty("server.ssl", "false");
        
        ServerConfig config = bind(props, "server", ServerConfig.class);
        System.out.println("Server config:");
        System.out.println("  port: " + config.port);
        System.out.println("  host: " + config.host);
        System.out.println("  maxConnections: " + config.maxConnections);
        System.out.println("  ssl: " + config.ssl);
    }
}
```

---

## Step 6: Application Context Lifecycle

```java
public class ApplicationContextLifecycle {
    // Simplified lifecycle phases
    enum Phase { CREATED, REFRESHED, STARTED, STOPPING, STOPPED }
    
    interface LifecycleListener {
        void onRefresh();
        void onStart();
        void onStop();
    }
    
    static class ApplicationContext {
        Phase phase = Phase.CREATED;
        final List<LifecycleListener> listeners = new ArrayList<>();
        final SimpleBeanFactory factory;
        
        ApplicationContext(Properties props) { factory = new SimpleBeanFactory(props); }
        
        void addListener(LifecycleListener l) { listeners.add(l); }
        
        void refresh() throws Exception {
            factory.register(DataSource.class, UserRepository.class, UserService.class);
            factory.refresh();
            phase = Phase.REFRESHED;
            listeners.forEach(LifecycleListener::onRefresh);
            System.out.println("Context refreshed. Beans: " + factory.getBeanNames());
        }
        
        void start() { phase = Phase.STARTED; listeners.forEach(LifecycleListener::onStart); }
        
        void stop() {
            phase = Phase.STOPPING;
            listeners.forEach(LifecycleListener::onStop);
            phase = Phase.STOPPED;
            System.out.println("Context stopped gracefully");
        }
        
        <T> T getBean(Class<T> type) { return factory.getBean(type); }
    }
    
    public static void main(String[] args) throws Exception {
        Properties props = new Properties();
        props.setProperty("db.url", "jdbc:sqlite:prod.db");
        props.setProperty("db.pool.size", "20");
        
        ApplicationContext ctx = new ApplicationContext(props);
        ctx.addListener(new LifecycleListener() {
            public void onRefresh() { System.out.println("[Event] Context refreshed"); }
            public void onStart()   { System.out.println("[Event] Context started"); }
            public void onStop()    { System.out.println("[Event] Context stopped"); }
        });
        
        ctx.refresh();
        ctx.start();
        
        UserService svc = ctx.getBean(UserService.class);
        System.out.println(svc.getUser(42));
        
        ctx.stop();
    }
}
```

---

## Step 7: Condition Evaluation

```java
import java.util.*;

public class ConditionEvaluation {
    // Equivalent to Spring's @ConditionalOnClass, @ConditionalOnMissingBean etc.
    @FunctionalInterface
    interface Condition {
        boolean matches(Properties env);
    }
    
    // @ConditionalOnClass equivalent
    static Condition onClass(String className) {
        return env -> {
            try {
                Class.forName(className);
                return true;
            } catch (ClassNotFoundException e) { return false; }
        };
    }
    
    // @ConditionalOnProperty equivalent
    static Condition onProperty(String key, String value) {
        return env -> value.equals(env.getProperty(key));
    }
    
    // @ConditionalOnMissingBean equivalent
    static Condition onMissingBean(Map<String, ?> beans, String beanName) {
        return env -> !beans.containsKey(beanName);
    }
    
    public static void main(String[] args) {
        Properties env = new Properties();
        env.setProperty("feature.async", "true");
        env.setProperty("cache.enabled", "false");
        
        System.out.println("onClass(java.sql.Connection): " +
            onClass("java.sql.Connection").matches(env));
        System.out.println("onClass(com.oracle.Driver): " +
            onClass("com.oracle.Driver").matches(env));
        System.out.println("onProperty(feature.async, true): " +
            onProperty("feature.async", "true").matches(env));
        System.out.println("onProperty(cache.enabled, true): " +
            onProperty("cache.enabled", "true").matches(env));
    }
}
```

---

## Step 8: Capstone — Manual DI Container

```java
import java.lang.annotation.*;
import java.lang.reflect.*;
import java.util.*;

@Retention(RetentionPolicy.RUNTIME) @interface Component { String value() default ""; }
@Retention(RetentionPolicy.RUNTIME) @interface Inject {}

@Component("dataSource")
class DataSource {
    public String getConnection() { return "jdbc:sqlite:app.db"; }
}

@Component("userRepository")
class UserRepository {
    @Inject DataSource dataSource;
    public String findUser(int id) { return "User[" + id + "] via " + dataSource.getConnection(); }
}

@Component("userService")
class UserService {
    @Inject UserRepository repo;
    public String getUser(int id) { return "Service -> " + repo.findUser(id); }
}

class DIContainer {
    Map<String, Object> beans = new HashMap<>();
    Map<Class<?>, Object> typeMap = new HashMap<>();
    
    void register(Class<?>... classes) throws Exception {
        for (Class<?> cls : classes) {
            Component ann = cls.getAnnotation(Component.class);
            String name = ann.value().isEmpty() ? lowerFirst(cls.getSimpleName()) : ann.value();
            Object bean = cls.getDeclaredConstructor().newInstance();
            beans.put(name, bean);
            typeMap.put(cls, bean);
        }
    }
    
    void wire() throws Exception {
        for (Object bean : beans.values()) {
            for (Field f : bean.getClass().getDeclaredFields()) {
                if (f.isAnnotationPresent(Inject.class)) {
                    f.setAccessible(true);
                    Object dep = typeMap.get(f.getType());
                    if (dep == null) throw new RuntimeException("No bean for: " + f.getType());
                    f.set(bean, dep);
                }
            }
        }
    }
    
    @SuppressWarnings("unchecked")
    <T> T get(String name) { return (T) beans.get(name); }
    
    static String lowerFirst(String s) { return Character.toLowerCase(s.charAt(0)) + s.substring(1); }
}

public class Main {
    public static void main(String[] args) throws Exception {
        DIContainer container = new DIContainer();
        container.register(DataSource.class, UserRepository.class, UserService.class);
        container.wire();
        
        System.out.println("Beans registered: " + container.beans.keySet());
        UserService svc = container.get("userService");
        System.out.println(svc.getUser(42));
        System.out.println(svc.getUser(99));
        System.out.println("Manual DI container: 3 beans wired via reflection");
    }
}
```

```bash
javac /tmp/Main.java -d /tmp && java -cp /tmp Main
```

📸 **Verified Output:**
```
Beans registered: [userRepository, dataSource, userService]
Service -> User[42] via jdbc:sqlite:app.db
Service -> User[99] via jdbc:sqlite:app.db
Manual DI container: 3 beans wired via reflection
```

---

## Summary

| Spring Concept | Manual Equivalent | Mechanism |
|---|---|---|
| `@Component` | Custom `@Component` annotation | `@Retention(RUNTIME)` |
| `@Autowired` | Custom `@Inject` annotation | `Field.set()` via reflection |
| `BeanFactory` | `SimpleBeanFactory` | `Map<String, Object>` |
| `ApplicationContext` | `ApplicationContext` class | Lifecycle phases |
| `@Value` | Custom `@Value` + property resolver | `Properties` lookup |
| `@ConditionalOnProperty` | `Condition` interface | `Properties.getProperty()` |
| `@PostConstruct` | Custom annotation | `Method.invoke()` |
| Configuration binding | `bind(props, prefix, class)` | Reflection field assignment |
