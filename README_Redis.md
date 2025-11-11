# Redis Connection Example with StackExchange.Redis

This project demonstrates how to connect to Redis Cloud using StackExchange.Redis in C#.

## Prerequisites

- .NET 8.0 or later
- A Redis Cloud instance (the example uses Redis Cloud configuration)

## Setup

1. **Install dependencies:**
   ```bash
   dotnet restore
   ```

2. **Update Redis credentials:**
   Edit the connection details in `RedisExample.cs` if you're using different Redis Cloud credentials.

## Usage

### Running the Example

```bash
dotnet run
```

This will execute three different connection examples:

1. **Basic synchronous connection** - Simple connect and set/get operations
2. **Connection string method** - Using a connection string format
3. **Async operations with error handling** - Recommended for production use

### Code Examples

#### Basic Connection
```csharp
var configuration = new ConfigurationOptions
{
    EndPoints = { { "your-redis-host", port } },
    User = "default",
    Password = "your-password"
};

var multiplexer = ConnectionMultiplexer.Connect(configuration);
var db = multiplexer.GetDatabase();

// Set and get values
db.StringSet("key", "value");
RedisValue result = db.StringGet("key");
```

#### Connection String
```csharp
string connectionString = "your-redis-host:port,password=your-password,user=default";
var multiplexer = ConnectionMultiplexer.Connect(connectionString);
```

#### Async Operations
```csharp
var multiplexer = await ConnectionMultiplexer.ConnectAsync(configuration);
var db = multiplexer.GetDatabase();

await db.StringSetAsync("key", "value");
RedisValue result = await db.StringGetAsync("key");
```

## Configuration Options

The example includes several important configuration options:

- `ConnectTimeout`: Connection timeout in milliseconds (default: 5000)
- `SyncTimeout`: Synchronous operation timeout (default: 5000)
- `ConnectRetry`: Number of connection retry attempts (default: 3)

## Error Handling

The async example demonstrates proper error handling:

```csharp
try
{
    var multiplexer = await ConnectionMultiplexer.ConnectAsync(configuration);
    // Your Redis operations here
}
catch (RedisConnectionException ex)
{
    Console.WriteLine($"Redis connection failed: {ex.Message}");
}
catch (Exception ex)
{
    Console.WriteLine($"An error occurred: {ex.Message}");
}
```

## Security Notes

- Never hardcode credentials in production code
- Use environment variables or secure configuration management
- Consider using Redis ACLs for fine-grained access control
- Enable TLS/SSL for production deployments

## Redis Cloud Configuration

This example is configured for Redis Cloud with:
- Host: `redis-16287.crce182.ap-south-1-1.ec2.redns.redis-cloud.com`
- Port: `16287`
- Authentication: User/password based

Update these values according to your Redis Cloud instance.
