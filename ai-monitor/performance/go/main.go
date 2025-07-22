package main

import (
	"fmt"
	"log"
	"net/http"
	"runtime"
	"time"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
)

// HealthResponse 健康检查响应
type HealthResponse struct {
	Status    string            `json:"status"`
	Timestamp int64             `json:"timestamp"`
	Version   string            `json:"version"`
	Service   string            `json:"service"`
	Uptime    int64             `json:"uptime"`
	System    map[string]interface{} `json:"system"`
}

// PerformanceResponse 性能测试响应
type PerformanceResponse struct {
	RequestID    string  `json:"request_id"`
	ProcessingNs int64   `json:"processing_ns"`
	ProcessingMs float64 `json:"processing_ms"`
	Timestamp    int64   `json:"timestamp"`
}

var startTime = time.Now()

func main() {
	// 设置Gin为发布模式以获得最佳性能
	gin.SetMode(gin.ReleaseMode)
	
	// 创建路由器
	router := gin.New()
	
	// 添加中间件
	router.Use(gin.Recovery())
	router.Use(cors.Default())
	
	// 添加自定义中间件进行性能监控
	router.Use(performanceMiddleware())
	
	// 路由配置
	router.GET("/health", healthHandler)
	router.GET("/performance", performanceHandler)
	router.POST("/process", processHandler)
	
	// API组
	v1 := router.Group("/api/v1")
	{
		v1.GET("/status", statusHandler)
		v1.POST("/compute", computeHandler)
	}
	
	// 启动服务器
	port := ":3001"
	log.Printf("🚀 Go闪电API启动在端口%s", port)
	log.Printf("📊 健康检查: http://localhost%s/health", port)
	log.Printf("⚡ 性能测试: http://localhost%s/performance", port)
	
	if err := router.Run(port); err != nil {
		log.Fatalf("服务器启动失败: %v", err)
	}
}

// 性能监控中间件
func performanceMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		
		// 处理请求
		c.Next()
		
		// 记录性能指标
		duration := time.Since(start)
		log.Printf("[%s] %s %s - %v", 
			c.Request.Method,
			c.Request.RequestURI,
			c.ClientIP(),
			duration)
	}
}

// 健康检查处理器
func healthHandler(c *gin.Context) {
	uptime := time.Since(startTime).Seconds()
	
	response := HealthResponse{
		Status:    "healthy",
		Timestamp: time.Now().Unix(),
		Version:   "1.0.0",
		Service:   "Go Lightning API",
		Uptime:    int64(uptime),
		System: map[string]interface{}{
			"go_version":     runtime.Version(),
			"num_goroutine": runtime.NumGoroutine(),
			"num_cpu":       runtime.NumCPU(),
			"arch":          runtime.GOARCH,
			"os":            runtime.GOOS,
		},
	}
	
	c.JSON(http.StatusOK, response)
}

// 性能测试处理器
func performanceHandler(c *gin.Context) {
	start := time.Now()
	
	// 模拟一些计算
	sum := 0
	for i := 0; i < 1000000; i++ {
		sum += i
	}
	
	processingTime := time.Since(start)
	
	response := PerformanceResponse{
		RequestID:    fmt.Sprintf("perf-%d", time.Now().UnixNano()),
		ProcessingNs: processingTime.Nanoseconds(),
		ProcessingMs: float64(processingTime.Nanoseconds()) / 1e6,
		Timestamp:    time.Now().Unix(),
	}
	
	c.JSON(http.StatusOK, response)
}

// 处理请求处理器
func processHandler(c *gin.Context) {
	var request map[string]interface{}
	
	if err := c.ShouldBindJSON(&request); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid request format",
		})
		return
	}
	
	// 快速处理并返回
	c.JSON(http.StatusOK, gin.H{
		"status":    "processed",
		"request":   request,
		"timestamp": time.Now().Unix(),
		"processor": "go-lightning",
	})
}

// 状态处理器
func statusHandler(c *gin.Context) {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	
	c.JSON(http.StatusOK, gin.H{
		"service": "AI Monitor Go Lightning API",
		"status":  "running",
		"memory": gin.H{
			"alloc_mb":      m.Alloc / 1024 / 1024,
			"total_alloc_mb": m.TotalAlloc / 1024 / 1024,
			"sys_mb":        m.Sys / 1024 / 1024,
			"gc_runs":       m.NumGC,
		},
		"runtime": gin.H{
			"goroutines": runtime.NumGoroutine(),
			"cpus":       runtime.NumCPU(),
			"go_version": runtime.Version(),
		},
	})
}

// 计算处理器 - 展示Go的并发能力
func computeHandler(c *gin.Context) {
	var request struct {
		Numbers []int `json:"numbers"`
		Workers int   `json:"workers"`
	}
	
	if err := c.ShouldBindJSON(&request); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request"})
		return
	}
	
	if request.Workers <= 0 {
		request.Workers = runtime.NumCPU()
	}
	
	start := time.Now()
	result := parallelSum(request.Numbers, request.Workers)
	duration := time.Since(start)
	
	c.JSON(http.StatusOK, gin.H{
		"result":      result,
		"workers":     request.Workers,
		"duration_ms": float64(duration.Nanoseconds()) / 1e6,
		"items":       len(request.Numbers),
	})
}

// 并行求和函数
func parallelSum(numbers []int, workers int) int64 {
	if len(numbers) == 0 {
		return 0
	}
	
	chunkSize := (len(numbers) + workers - 1) / workers
	results := make(chan int64, workers)
	
	for i := 0; i < workers; i++ {
		start := i * chunkSize
		end := start + chunkSize
		if end > len(numbers) {
			end = len(numbers)
		}
		
		go func(nums []int) {
			sum := int64(0)
			for _, n := range nums {
				sum += int64(n)
			}
			results <- sum
		}(numbers[start:end])
	}
	
	total := int64(0)
	for i := 0; i < workers; i++ {
		total += <-results
	}
	
	return total
}
