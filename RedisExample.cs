using StackExchange.Redis;

public class ConnectBasicExample
{
    public void Run()
    {
        // Create a connection to Redis Cloud
        var configuration = new ConfigurationOptions
        {
            EndPoints = { { "redis-16287.crce182.ap-south-1-1.ec2.redns.redis-cloud.com", 16287 } },
            User = "default",
            Password = "dhokTpjWXB3yQLkvngkY59chsTcKyvb6"
        };

        var multiplexer = ConnectionMultiplexer.Connect(configuration);
        var db = multiplexer.GetDatabase();

        // Set a key-value pair
        db.StringSet("foo", "bar");

        // Get the value back
        RedisValue result = db.StringGet("foo");
        Console.WriteLine(result); // >>> bar

        // Clean up
        multiplexer.Close();
    }

    // Alternative method with connection string
    public void RunWithConnectionString()
    {
        // Using connection string format
        string connectionString = "redis-16287.crce182.ap-south-1-1.ec2.redns.redis-cloud.com:16287,password=dhokTpjWXB3yQLkvngkY59chsTcKyvb6,user=default";

        var multiplexer = ConnectionMultiplexer.Connect(connectionString);
        var db = multiplexer.GetDatabase();

        // Set a key-value pair
        db.StringSet("example", "value");

        // Get the value back
        RedisValue result = db.StringGet("example");
        Console.WriteLine(result); // >>> value

        // Clean up
        multiplexer.Close();
    }

    // Example with error handling and async operations
    public async Task RunAsync()
    {
        try
        {
            var configuration = new ConfigurationOptions
            {
                EndPoints = { { "redis-16287.crce182.ap-south-1-1.ec2.redns.redis-cloud.com", 16287 } },
                User = "default",
                Password = "dhokTpjWXB3yQLkvngkY59chsTcKyvb6",
                // Additional configuration for reliability
                ConnectTimeout = 5000,
                SyncTimeout = 5000,
                ConnectRetry = 3
            };

            var multiplexer = await ConnectionMultiplexer.ConnectAsync(configuration);
            var db = multiplexer.GetDatabase();

            // Async operations
            await db.StringSetAsync("async_key", "async_value");
            RedisValue result = await db.StringGetAsync("async_key");

            Console.WriteLine($"Async result: {result}");

            // Clean up
            await multiplexer.CloseAsync();
        }
        catch (RedisConnectionException ex)
        {
            Console.WriteLine($"Redis connection failed: {ex.Message}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"An error occurred: {ex.Message}");
        }
    }
}
