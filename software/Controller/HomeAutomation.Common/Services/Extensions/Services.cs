using HomeAutomation.Common.Configuration;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using NLog.Extensions.Logging;
using System.Reflection;

namespace HomeAutomation.Common.Services.Extensions
{
  public class Services : IServiceProvider
  {
    private readonly IServiceProvider _serviceProvider;

    public Services()
    {
      string exeDirectory = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location) ?? string.Empty;

      // Build a config object, using env vars and JSON providers.
      var configBuilder = new ConfigurationBuilder()
          .SetBasePath(Directory.GetCurrentDirectory())
          .AddJsonFile(Path.Combine(exeDirectory, "appsettings.json"))
          .AddJsonFile(Path.Combine(exeDirectory, $"appsettings.{HostEnvironment.EnvironmentName}.json"), true, false)
          .AddEnvironmentVariables();

      // Build the config from json settings
      var configuration = configBuilder.Build();

      var services = new ServiceCollection();

      ConfigureServices(services);

      // Configure logging for this method (prior to real one being built).
      var loggingSection = configuration.GetSection("logging");
      _serviceProvider = ConfigureLogging(services, loggingSection);

      var apiDevices = new ApiDevices();
      configuration.Bind(nameof(ApiDevices), apiDevices);

      services.AddSingleton(apiDevices);
    }

    public T GetRequiredService<T>() where T : notnull
    {
      return _serviceProvider.GetRequiredService<T>();
    }

    public T? GetService<T>()
    {
      return _serviceProvider.GetService<T>();
    }

    public object? GetService(Type serviceType)
    {
      return _serviceProvider.GetService(serviceType);
    }

    public IServiceProvider GetServiceProvider()
    {
      return _serviceProvider;
    }

    private static IServiceProvider ConfigureLogging(ServiceCollection services, IConfiguration configuration)
    {
      services.AddLogging(loggingBuilder =>
      {
        // Get the NLog config section
        var nlogSection = configuration.GetSection("NLog");

        // Set NLog configuration
        NLog.LogManager.Configuration = new NLogLoggingConfiguration(nlogSection);

        // Configure .NET logging
        loggingBuilder
            .AddConfiguration(configuration)
            .AddNLog();
      });

      var serviceProvider = services.BuildServiceProvider();
      return serviceProvider;
    }

    private static void ConfigureServices(ServiceCollection _ /* services */)
    {
    }
  }
}
