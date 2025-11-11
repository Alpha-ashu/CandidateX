using System;
using System.Threading.Tasks;

class Program
{
    static async Task Main(string[] args)
    {
        Console.WriteLine("Redis Connection Example");
        Console.WriteLine("========================");

        var example = new ConnectBasicExample();

        try
        {
            // Run the basic synchronous example
            Console.WriteLine("\n1. Running basic synchronous example:");
            example.Run();

            // Run the connection string example
            Console.WriteLine("\n2. Running connection string example:");
            example.RunWithConnectionString();

            // Run the async example
            Console.WriteLine("\n3. Running async example:");
            await example.RunAsync();

            Console.WriteLine("\nAll examples completed successfully!");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"An error occurred: {ex.Message}");
        }
    }
}
