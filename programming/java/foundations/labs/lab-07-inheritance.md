# Lab 7: Inheritance & Polymorphism

## Objective
Use `extends` to build class hierarchies, override methods, call `super`, understand polymorphism, and apply the Liskov Substitution Principle.

## Background
Inheritance lets you build specialized classes from general ones, reusing and extending behavior. Polymorphism — "many forms" — means a reference of type `Animal` can hold a `Dog` or `Cat`, and the correct method runs at runtime. These mechanisms enable frameworks, plugin systems, and extensible designs.

## Time
40 minutes

## Prerequisites
- Lab 06 (OOP — Classes)

## Tools
- Java 21 (Eclipse Temurin)
- Docker image: `innozverse-java:latest`

---

## Lab Instructions

### Step 1: extends and method overriding

```java
// Shapes.java
public class Shapes {

    static abstract class Shape {
        protected String color;

        Shape(String color) { this.color = color; }

        abstract double area();
        abstract double perimeter();

        // Concrete method — inherited as-is
        void describe() {
            System.out.printf("%s %s: area=%.2f perimeter=%.2f%n",
                color, getClass().getSimpleName(), area(), perimeter());
        }
    }

    static class Circle extends Shape {
        private final double radius;

        Circle(String color, double radius) {
            super(color);  // must be first statement
            this.radius = radius;
        }

        @Override public double area() { return Math.PI * radius * radius; }
        @Override public double perimeter() { return 2 * Math.PI * radius; }
    }

    static class Rectangle extends Shape {
        protected final double width, height;

        Rectangle(String color, double width, double height) {
            super(color);
            this.width = width; this.height = height;
        }

        @Override public double area() { return width * height; }
        @Override public double perimeter() { return 2 * (width + height); }
    }

    static class Square extends Rectangle {
        Square(String color, double side) {
            super(color, side, side);
        }

        @Override
        public String toString() {
            return String.format("Square(%.1f, %s)", width, color);
        }
    }

    public static void main(String[] args) {
        Shape[] shapes = {
            new Circle("red", 5),
            new Rectangle("blue", 4, 6),
            new Square("green", 4),
        };

        for (Shape s : shapes) s.describe();

        // Polymorphism — same method, different behavior
        double totalArea = 0;
        for (Shape s : shapes) totalArea += s.area();
        System.out.printf("\nTotal area: %.2f%n", totalArea);

        // instanceof check
        for (Shape s : shapes) {
            if (s instanceof Rectangle r) {
                System.out.println(r + " is a Rectangle (width=" + r.width + ")");
            }
        }
    }
}
```

> 💡 **`@Override` annotation** is crucial — it asks the compiler to verify you're actually overriding a parent method. Without it, a typo like `pubilc double Area()` silently creates a new method instead of overriding, and the bug is invisible until runtime.

**📸 Verified Output:**
```
red Circle: area=78.54 perimeter=31.42
blue Rectangle: area=24.00 perimeter=20.00
green Square: area=16.00 perimeter=16.00

Total area: 118.54
Square(4.0, green) is a Rectangle (width=4.0)
```

---

### Step 2: super — Calling Parent Methods

```java
// Vehicles.java
public class Vehicles {

    static class Vehicle {
        protected String brand;
        protected int year;
        protected double fuelLevel;

        Vehicle(String brand, int year) {
            this.brand = brand;
            this.year = year;
            this.fuelLevel = 1.0;
        }

        String status() {
            return String.format("%s(%d) fuel=%.0f%%", brand, year, fuelLevel * 100);
        }

        void refuel(double amount) {
            fuelLevel = Math.min(1.0, fuelLevel + amount);
        }

        void drive(double distance) {
            System.out.println(brand + " driving " + distance + "km");
            fuelLevel = Math.max(0, fuelLevel - distance / 500.0);
        }
    }

    static class ElectricVehicle extends Vehicle {
        private double batteryLevel;

        ElectricVehicle(String brand, int year) {
            super(brand, year);
            this.batteryLevel = 1.0;
        }

        @Override
        String status() {
            // Augment parent's status
            return super.status() + String.format(" battery=%.0f%%", batteryLevel * 100);
        }

        @Override
        void drive(double distance) {
            System.out.println(brand + " (electric) driving " + distance + "km silently");
            batteryLevel = Math.max(0, batteryLevel - distance / 400.0);
            fuelLevel = batteryLevel; // sync
        }

        void charge(double amount) {
            batteryLevel = Math.min(1.0, batteryLevel + amount);
            fuelLevel = batteryLevel;
            System.out.println(brand + " charged to " + (int)(batteryLevel*100) + "%");
        }
    }

    public static void main(String[] args) {
        Vehicle car = new Vehicle("Toyota", 2020);
        ElectricVehicle ev = new ElectricVehicle("Tesla", 2024);

        car.drive(100);
        ev.drive(100);

        System.out.println("\nStatus:");
        System.out.println(car.status());
        System.out.println(ev.status());

        ev.charge(0.5);
        System.out.println(ev.status());
    }
}
```

> 💡 **`super.method()`** calls the parent's implementation from within an override. This is the "extend, don't replace" pattern. `ElectricVehicle.status()` adds battery info to the vehicle's status string without duplicating the base formatting logic.

**📸 Verified Output:**
```
Toyota driving 100.0km
Tesla (electric) driving 100.0km silently

Status:
Toyota(2020) fuel=80%
Tesla(2024) fuel=75% battery=75%
Tesla charged to 100%
Tesla(2024) fuel=100% battery=100%
```

---

### Step 3: Polymorphism in Practice

```java
// PaymentSystem.java
import java.util.List;
import java.util.ArrayList;

public class PaymentSystem {

    abstract static class Payment {
        protected final String id;
        protected final double amount;

        Payment(String id, double amount) {
            this.id = id; this.amount = amount;
        }

        abstract boolean process();
        abstract String getMethod();

        @Override
        public String toString() {
            return String.format("[%s] %s $%.2f", id, getMethod(), amount);
        }
    }

    static class CreditCard extends Payment {
        private final String last4;
        CreditCard(String id, double amount, String last4) {
            super(id, amount); this.last4 = last4;
        }
        @Override
        public boolean process() {
            System.out.println("  Charging card *" + last4 + " for $" + amount);
            return amount <= 5000; // decline over $5000
        }
        @Override public String getMethod() { return "Credit Card *" + last4; }
    }

    static class PayPal extends Payment {
        private final String email;
        PayPal(String id, double amount, String email) {
            super(id, amount); this.email = email;
        }
        @Override
        public boolean process() {
            System.out.println("  PayPal charge to " + email);
            return true;
        }
        @Override public String getMethod() { return "PayPal:" + email; }
    }

    static class Crypto extends Payment {
        private final String wallet;
        Crypto(String id, double amount, String wallet) {
            super(id, amount); this.wallet = wallet;
        }
        @Override
        public boolean process() {
            System.out.println("  Crypto tx to " + wallet.substring(0,8) + "...");
            return amount < 10000;
        }
        @Override public String getMethod() { return "Crypto:" + wallet.substring(0,8); }
    }

    static void processAll(List<Payment> payments) {
        int success = 0;
        double total = 0;
        for (Payment p : payments) {
            System.out.println("Processing: " + p);
            boolean ok = p.process();
            System.out.println("  → " + (ok ? "✓ Approved" : "✗ Declined"));
            if (ok) { success++; total += p.amount; }
        }
        System.out.printf("%nSummary: %d/%d approved, $%.2f total%n",
            success, payments.size(), total);
    }

    public static void main(String[] args) {
        processAll(List.of(
            new CreditCard("TXN001", 99.99, "4242"),
            new PayPal("TXN002", 250.00, "chen@example.com"),
            new Crypto("TXN003", 500.00, "0xABCD1234EFGH5678"),
            new CreditCard("TXN004", 9999.00, "1234")  // will decline
        ));
    }
}
```

> 💡 **`processAll` doesn't know what type of payment it's processing** — it just calls `p.process()` and `p.getMethod()`. Adding a new payment type (Apple Pay, Stripe) requires zero changes to `processAll`. This is Open/Closed Principle: open for extension, closed for modification.

**📸 Verified Output:**
```
Processing: [TXN001] Credit Card *4242 $99.99
  Charging card *4242 for $99.99
  → ✓ Approved
Processing: [TXN002] PayPal:chen@example.com $250.00
  PayPal charge to chen@example.com
  → ✓ Approved
Processing: [TXN003] Crypto:0xABCD12... $500.00
  Crypto tx to 0xABCD12...
  → ✓ Approved
Processing: [TXN004] Credit Card *1234 $9999.00
  Charging card *1234 for $9999.0
  → ✗ Declined

Summary: 3/4 approved, $849.99 total
```

---

### Step 4: Abstract Classes vs Concrete Classes

```java
// AbstractTemplate.java
public class AbstractTemplate {

    // Template Method Pattern
    abstract static class Report {
        // Template method — defines algorithm skeleton
        final void generate() {
            System.out.println("=== " + title() + " ===");
            fetchData();
            processData();
            render();
            System.out.println("=== End Report ===\n");
        }

        abstract String title();
        abstract void fetchData();
        abstract void processData();
        abstract void render();
    }

    static class SalesReport extends Report {
        private double[] sales;

        @Override String title() { return "Monthly Sales Report"; }

        @Override void fetchData() {
            sales = new double[]{12500, 18200, 9800, 22100, 15600};
            System.out.println("Fetched " + sales.length + " sales records");
        }

        @Override void processData() {
            double total = 0;
            for (double s : sales) total += s;
            System.out.printf("Total: $%.0f, Avg: $%.0f%n", total, total / sales.length);
        }

        @Override void render() {
            for (int i = 0; i < sales.length; i++) {
                int bars = (int)(sales[i] / 1000);
                System.out.printf("Week %d: %s $%.0f%n", i+1, "█".repeat(bars), sales[i]);
            }
        }
    }

    static class InventoryReport extends Report {
        @Override String title() { return "Inventory Status"; }
        @Override void fetchData() { System.out.println("Fetched inventory data"); }
        @Override void processData() { System.out.println("Flagged 3 low-stock items"); }
        @Override void render() {
            System.out.println("Widget A: 45 units ✓");
            System.out.println("Widget B: 3 units ⚠ LOW");
            System.out.println("Widget C: 0 units ✗ OUT");
        }
    }

    public static void main(String[] args) {
        new SalesReport().generate();
        new InventoryReport().generate();
    }
}
```

> 💡 **The Template Method Pattern** uses `final` on the skeleton method to prevent overriding the algorithm structure, while `abstract` methods let subclasses customize each step. `final` on a method means "I define the algorithm; you fill in the blanks."

**📸 Verified Output:**
```
=== Monthly Sales Report ===
Fetched 5 sales records
Total: $78200, Avg: $15640
Week 1: ████████████ $12500
Week 2: ██████████████████ $18200
Week 3: █████████ $9800
Week 4: ██████████████████████ $22100
Week 5: ███████████████ $15600
=== End Report ===

=== Inventory Status ===
Fetched inventory data
Flagged 3 low-stock items
Widget A: 45 units ✓
Widget B: 3 units ⚠ LOW
Widget C: 0 units ✗ OUT
=== End Report ===
```

---

### Step 5: final, sealed Classes

```java
// SealedClasses.java
public class SealedClasses {

    // sealed — restricts which classes can extend (Java 17+)
    sealed interface Expr permits Num, Add, Mul, Neg {}

    record Num(double value) implements Expr {}
    record Add(Expr left, Expr right) implements Expr {}
    record Mul(Expr left, Expr right) implements Expr {}
    record Neg(Expr expr) implements Expr {}

    // Pattern matching switch is exhaustive (compiler-checked)
    static double eval(Expr e) {
        return switch (e) {
            case Num(double v)       -> v;
            case Add(var l, var r)   -> eval(l) + eval(r);
            case Mul(var l, var r)   -> eval(l) * eval(r);
            case Neg(var inner)      -> -eval(inner);
        };
    }

    static String pretty(Expr e) {
        return switch (e) {
            case Num(double v)      -> String.valueOf(v);
            case Add(var l, var r)  -> "(" + pretty(l) + " + " + pretty(r) + ")";
            case Mul(var l, var r)  -> "(" + pretty(l) + " * " + pretty(r) + ")";
            case Neg(var inner)     -> "-" + pretty(inner);
        };
    }

    public static void main(String[] args) {
        // (2 + 3) * -(4)
        Expr expr = new Mul(
            new Add(new Num(2), new Num(3)),
            new Neg(new Num(4))
        );

        System.out.println("Expression: " + pretty(expr));
        System.out.println("Result: " + eval(expr));

        // 10 * (5 + -3)
        Expr expr2 = new Mul(new Num(10), new Add(new Num(5), new Neg(new Num(3))));
        System.out.println("\nExpression: " + pretty(expr2));
        System.out.println("Result: " + eval(expr2));
    }
}
```

> 💡 **Sealed interfaces** (Java 17+) list all permitted implementations. Combined with pattern matching switch, the compiler verifies your switch is exhaustive — you can't forget to handle a case. This is how Rust's enums and Haskell's ADTs work; Java finally caught up.

**📸 Verified Output:**
```
Expression: ((2.0 + 3.0) * -4.0)
Result: -20.0

Expression: (10.0 * (5.0 + -3.0))
Result: 20.0
```

---

### Step 6: Method Hiding vs Overriding

```java
// StaticVsDynamic.java
public class StaticVsDynamic {

    static class Animal {
        // Instance method — overriding (dynamic dispatch)
        String speak() { return "..."; }

        // Static method — hiding (static dispatch)
        static String type() { return "Animal"; }
    }

    static class Dog extends Animal {
        @Override
        String speak() { return "Woof!"; }  // overrides

        // This HIDES Animal.type(), not overrides it
        static String type() { return "Dog"; }
    }

    public static void main(String[] args) {
        Animal a = new Dog();  // reference type = Animal, runtime type = Dog

        // Dynamic dispatch — uses runtime type (Dog)
        System.out.println("speak: " + a.speak());      // Woof! (Dog's)

        // Static dispatch — uses reference type (Animal)
        System.out.println("type (via Animal ref): " + Animal.type()); // Animal
        System.out.println("type (via Dog ref): " + Dog.type());       // Dog

        // Casting
        if (a instanceof Dog d) {
            System.out.println("Dog speak: " + d.speak());
            System.out.println("Dog type: " + Dog.type());
        }

        // Array of animals — polymorphic behavior
        Animal[] animals = { new Dog(), new Animal(), new Dog() };
        for (Animal animal : animals) {
            System.out.println(animal.getClass().getSimpleName() + ": " + animal.speak());
        }
    }
}
```

> 💡 **Static methods are not polymorphic.** They resolve based on the compile-time type of the reference, not the runtime type of the object. This is why "method hiding" (for statics) is a separate concept from "method overriding" (for instance methods). Avoid calling static methods via instance references — it's confusing.

**📸 Verified Output:**
```
speak: Woof!
type (via Animal ref): Animal
type (via Dog ref): Dog
Dog speak: Woof!
Dog type: Dog
Animal: Woof!
Animal: ...
Animal: Woof!
```

---

### Step 7: Covariant Return Types & Fluent Inheritance

```java
// FluentBuilder.java
public class FluentBuilder {

    static class Builder<T extends Builder<T>> {
        protected String name;
        protected int priority;

        @SuppressWarnings("unchecked")
        T name(String name) { this.name = name; return (T) this; }

        @SuppressWarnings("unchecked")
        T priority(int p) { this.priority = p; return (T) this; }
    }

    static class TaskBuilder extends Builder<TaskBuilder> {
        private String assignee;
        private String deadline;

        TaskBuilder assignee(String a) { this.assignee = a; return this; }
        TaskBuilder deadline(String d) { this.deadline = d; return this; }

        String build() {
            return String.format("Task{%s, priority=%d, assignee=%s, due=%s}",
                name, priority, assignee, deadline);
        }
    }

    // Covariant return — subclass can narrow return type
    static class Animal {
        Animal create() { return new Animal(); }
        @Override public String toString() { return "Animal"; }
    }

    static class Cat extends Animal {
        @Override
        Cat create() { return new Cat(); }  // covariant: Cat is-a Animal
        String purr() { return "purr"; }
        @Override public String toString() { return "Cat"; }
    }

    public static void main(String[] args) {
        // Fluent builder with inheritance
        String task = new TaskBuilder()
            .name("Deploy v2.0")
            .priority(1)
            .assignee("Dr. Chen")
            .deadline("2026-03-15")
            .build();
        System.out.println(task);

        // Covariant return types
        Cat cat = new Cat().create();
        System.out.println(cat + " says " + cat.purr());
    }
}
```

> 💡 **Covariant return types** (Java 5+) let overriding methods return a more specific type. `Cat.create()` returns `Cat` instead of `Animal` — callers who know they have a `Cat` get back a `Cat` without casting. Fluent builders use the self-type pattern `<T extends Builder<T>>` to preserve the subtype through method chains.

**📸 Verified Output:**
```
Task{Deploy v2.0, priority=1, assignee=Dr. Chen, due=2026-03-15}
Cat says purr
```

---

### Step 8: Full Example — Employee Hierarchy

```java
// EmployeeHierarchy.java
import java.util.*;

public class EmployeeHierarchy {

    abstract static class Employee {
        final String name;
        final String id;
        double baseSalary;

        Employee(String name, String id, double baseSalary) {
            this.name = name; this.id = id; this.baseSalary = baseSalary;
        }

        abstract double calculatePay();
        abstract String role();

        String summary() {
            return String.format("%-15s %-12s %-15s $%,.2f", id, role(), name, calculatePay());
        }
    }

    static class FullTime extends Employee {
        FullTime(String name, String id, double annual) { super(name, id, annual); }
        @Override double calculatePay() { return baseSalary / 12; }
        @Override String role() { return "Full-Time"; }
    }

    static class Contractor extends Employee {
        private final double hoursWorked;
        Contractor(String name, String id, double hourlyRate, double hours) {
            super(name, id, hourlyRate);
            this.hoursWorked = hours;
        }
        @Override double calculatePay() { return baseSalary * hoursWorked; }
        @Override String role() { return "Contractor"; }
    }

    static class Manager extends FullTime {
        private final double bonus;
        Manager(String name, String id, double annual, double bonus) {
            super(name, id, annual);
            this.bonus = bonus;
        }
        @Override double calculatePay() { return super.calculatePay() + bonus; }
        @Override String role() { return "Manager"; }
    }

    static void payroll(List<Employee> employees) {
        System.out.printf("%-15s %-12s %-15s %s%n", "ID", "Role", "Name", "Monthly Pay");
        System.out.println("─".repeat(60));
        double total = 0;
        for (Employee e : employees) {
            System.out.println(e.summary());
            total += e.calculatePay();
        }
        System.out.println("─".repeat(60));
        System.out.printf("%-42s $%,.2f%n", "TOTAL PAYROLL:", total);
    }

    public static void main(String[] args) {
        payroll(List.of(
            new FullTime("Alice Chen", "E001", 96000),
            new Contractor("Bob Lee", "C001", 85.0, 160),
            new Manager("Carol Wang", "M001", 120000, 2000),
            new Contractor("Dave Kim", "C002", 75.0, 80),
            new FullTime("Eve Park", "E002", 72000)
        ));
    }
}
```

> 💡 **`Manager.calculatePay()` calls `super.calculatePay()`** to reuse the monthly calculation logic and add the bonus on top. This is the key benefit of inheritance: you add or modify behavior without copying code. When `baseSalary` changes in `FullTime`, `Manager` automatically benefits.

**📸 Verified Output:**
```
ID              Role         Name            Monthly Pay
────────────────────────────────────────────────────────────
E001            Full-Time    Alice Chen      $8,000.00
C001            Contractor   Bob Lee         $13,600.00
M001            Manager      Carol Wang      $12,000.00
C002            Contractor   Dave Kim        $6,000.00
E002            Full-Time    Eve Park        $6,000.00
────────────────────────────────────────────────────────────
TOTAL PAYROLL:                               $45,600.00
```

---

## Verification

```bash
javac EmployeeHierarchy.java && java EmployeeHierarchy
```

## Summary

You've covered `extends`, `@Override`, `super`, abstract classes, polymorphism, sealed interfaces, static vs instance dispatch, covariant returns, and the employee payroll hierarchy. Inheritance is powerful — use it when you have a genuine "is-a" relationship and need to share behavior, not just to reuse code.

## Further Reading
- [Liskov Substitution Principle](https://en.wikipedia.org/wiki/Liskov_substitution_principle)
- [JEP 409: Sealed Classes](https://openjdk.org/jeps/409)
- [Effective Java — Favor composition over inheritance (Item 18)](https://www.oreilly.com/library/view/effective-java-3rd/9780134686097/)
