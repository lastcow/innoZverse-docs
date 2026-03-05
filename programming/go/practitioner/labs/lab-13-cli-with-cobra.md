# Lab 13: CLI with Cobra

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm golang:1.22-alpine sh`

## Overview

Build a fully-featured CLI application using [Cobra](https://github.com/spf13/cobra) — the same framework powering `kubectl`, `docker`, and `hugo`. Add Viper for config management, subcommands, and shell completion.

---

## Step 1: Project Setup

```bash
mkdir mycli && cd mycli
go mod init mycli
go get github.com/spf13/cobra@latest
go get github.com/spf13/viper@latest
```

Directory structure:

```
mycli/
├── main.go
├── cmd/
│   ├── root.go
│   ├── serve.go
│   └── version.go
└── go.mod
```

> 💡 Cobra conventionally places each command in its own file under `cmd/`. This keeps each command self-contained and testable.

---

## Step 2: Root Command with Persistent Flags

**`cmd/root.go`**:

```go
package cmd

import (
    "fmt"
    "os"

    "github.com/spf13/cobra"
    "github.com/spf13/viper"
)

var cfgFile string

var rootCmd = &cobra.Command{
    Use:   "mycli",
    Short: "mycli — a demo CLI built with cobra",
    Long: `mycli is a production-style CLI demonstrating:
  - Subcommands with cobra.Command
  - Persistent flags (global to all subcommands)
  - Viper config integration
  - Shell completion`,
}

func Execute() {
    if err := rootCmd.Execute(); err != nil {
        fmt.Fprintln(os.Stderr, err)
        os.Exit(1)
    }
}

func init() {
    cobra.OnInitialize(initConfig)

    // Persistent flags apply to root and ALL subcommands
    rootCmd.PersistentFlags().StringVar(&cfgFile, "config", "", "config file (default: config.yaml)")
    rootCmd.PersistentFlags().Bool("verbose", false, "enable verbose output")

    // Bind flag to viper so it's accessible anywhere
    viper.BindPFlag("verbose", rootCmd.PersistentFlags().Lookup("verbose"))
}

func initConfig() {
    if cfgFile != "" {
        viper.SetConfigFile(cfgFile)
    } else {
        viper.SetConfigName("config")
        viper.SetConfigType("yaml")
        viper.AddConfigPath(".")
    }
    viper.SetDefault("server.port", 8080)
    viper.SetDefault("server.host", "0.0.0.0")
    viper.AutomaticEnv() // e.g. MYCLI_SERVER_PORT overrides server.port
    viper.ReadInConfig()
}
```

---

## Step 3: `serve` Subcommand

**`cmd/serve.go`**:

```go
package cmd

import (
    "fmt"

    "github.com/spf13/cobra"
    "github.com/spf13/viper"
)

var serveCmd = &cobra.Command{
    Use:   "serve",
    Short: "Start the HTTP server",
    Long:  "Start the HTTP API server with configurable host and port.",
    RunE: func(cmd *cobra.Command, args []string) error {
        port, _ := cmd.Flags().GetInt("port")
        host := viper.GetString("server.host")
        verbose := viper.GetBool("verbose")

        if verbose {
            fmt.Printf("[verbose] Starting server with config: %s\n", viper.ConfigFileUsed())
        }
        fmt.Printf("Starting server on %s:%d\n", host, port)
        return nil
    },
}

func init() {
    rootCmd.AddCommand(serveCmd)
    serveCmd.Flags().IntP("port", "p", 8080, "port to listen on")
    // Bind --port flag to viper key for config file fallback
    viper.BindPFlag("server.port", serveCmd.Flags().Lookup("port"))
}
```

---

## Step 4: `version` Subcommand

**`cmd/version.go`**:

```go
package cmd

import (
    "fmt"
    "runtime"

    "github.com/spf13/cobra"
)

var Version = "1.0.0"

var versionCmd = &cobra.Command{
    Use:   "version",
    Short: "Print version information",
    Run: func(cmd *cobra.Command, args []string) {
        fmt.Printf("mycli version %s (%s)\n", Version, runtime.Version())
    },
}

func init() {
    rootCmd.AddCommand(versionCmd)
}
```

---

## Step 5: Positional Args Validation

Add a `greet` subcommand that requires exactly one positional argument:

```go
var greetCmd = &cobra.Command{
    Use:   "greet [name]",
    Short: "Greet a user by name",
    Args:  cobra.ExactArgs(1), // enforces exactly 1 positional arg
    RunE: func(cmd *cobra.Command, args []string) error {
        shout, _ := cmd.Flags().GetBool("shout")
        msg := "Hello, " + args[0] + "!"
        if shout {
            msg = strings.ToUpper(msg)
        }
        fmt.Println(msg)
        return nil
    },
}

func init() {
    rootCmd.AddCommand(greetCmd)
    greetCmd.Flags().Bool("shout", false, "print in uppercase")
}
```

> 💡 Cobra provides: `cobra.NoArgs`, `cobra.ExactArgs(n)`, `cobra.MinimumNArgs(n)`, `cobra.MaximumNArgs(n)`, `cobra.RangeArgs(min, max)`.

---

## Step 6: Shell Completion

Cobra generates shell completion automatically:

```bash
# Bash
mycli completion bash > /etc/bash_completion.d/mycli

# Zsh
mycli completion zsh > "${fpath[1]}/_mycli"

# Fish
mycli completion fish | source

# PowerShell
mycli completion powershell | Out-String | Invoke-Expression
```

The `completion` command is registered automatically when you call `rootCmd.Execute()`.

---

## Step 7: Viper Config File Integration

**`config.yaml`** (auto-loaded from `.`):

```yaml
server:
  host: "0.0.0.0"
  port: 9090
verbose: true
```

Priority order (highest → lowest):
1. Explicit `--flag` value
2. Environment variable (`MYCLI_SERVER_PORT`)
3. Config file (`config.yaml`)
4. `viper.SetDefault()`

```go
// Reading config values anywhere in your app:
port := viper.GetInt("server.port")    // 9090 from file
host := viper.GetString("server.host") // "0.0.0.0"
```

---

## Step 8 (Capstone): Full CLI Demo

**Simulated CLI behavior (Docker-runnable without network):**

```bash
docker run --rm golang:1.22-alpine sh -c "
cat > /tmp/cobra_sim.go << 'GOEOF'
package main

import (
    \"fmt\"
    \"os\"
)

func main() {
    args := os.Args[1:]
    if len(args) == 0 {
        fmt.Println(\"mycli - A demo CLI built with cobra\")
        fmt.Println()
        fmt.Println(\"Usage:\")
        fmt.Println(\"  mycli [command]\")
        fmt.Println()
        fmt.Println(\"Available Commands:\")
        fmt.Println(\"  serve       Start the HTTP server\")
        fmt.Println(\"  version     Print version info\")
        fmt.Println()
        fmt.Println(\"Flags:\")
        fmt.Println(\"  --config string   config file (default: config.yaml)\")
        fmt.Println(\"  --verbose         enable verbose output\")
        return
    }
    switch args[0] {
    case \"serve\":
        port := \"8080\"
        verbose := false
        for i, a := range args {
            if a == \"--port\" && i+1 < len(args) { port = args[i+1] }
            if a == \"--verbose\" { verbose = true }
        }
        if verbose { fmt.Println(\"[verbose] Starting server with config: config.yaml\") }
        fmt.Printf(\"Starting server on :%s\n\", port)
    case \"version\":
        fmt.Println(\"mycli version 1.0.0 (go1.22)\")
    default:
        fmt.Println(\"Unknown command:\", args[0])
        os.Exit(1)
    }
}
GOEOF
cd /tmp && go run cobra_sim.go
echo '---'
go run cobra_sim.go serve --port 9090 --verbose
echo '---'
go run cobra_sim.go version
"
```

📸 Verified Output:
```
mycli - A demo CLI built with cobra

Usage:
  mycli [command]

Available Commands:
  serve       Start the HTTP server
  version     Print version info

Flags:
  --config string   config file (default: config.yaml)
  --verbose         enable verbose output
---
[verbose] Starting server with config: config.yaml
Starting server on :9090
---
mycli version 1.0.0 (go1.22)
```

---

## Summary

| Concept | Cobra API | Purpose |
|---------|-----------|---------|
| Command definition | `cobra.Command{Use, Short, Long, RunE}` | Define CLI commands |
| Persistent flags | `PersistentFlags().StringVar/BoolVar/IntVar` | Flags shared by all subcommands |
| Local flags | `Flags().IntP("port", "p", 8080, ...)` | Flags scoped to one command |
| Subcommands | `rootCmd.AddCommand(serveCmd)` | Hierarchical commands |
| Config management | `viper.SetDefault/GetString/BindPFlag` | File + env + flag merging |
| Args validation | `cobra.ExactArgs(n)` | Enforce positional arg count |
| Shell completion | `mycli completion bash` | Auto-generated completions |
