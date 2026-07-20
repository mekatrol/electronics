using Microsoft.Extensions.Logging;

namespace HomeAutomation.Common.Services.Extensions
{
  public static class LoggingExtensions
  {
    public static void LogError(this ILogger logger, Exception ex)
    {
      logger.LogError(ex, "{Message}", ex.Message);
    }

    public static void LogWarning(this ILogger logger, Exception ex)
    {
      logger.LogWarning(ex, "{Message}", ex.Message);
    }

    public static void LogInformation(this ILogger logger, Exception ex)
    {
      logger.LogInformation(ex, "{Message}", ex.Message);
    }

    public static void LogDebug(this ILogger logger, Exception ex)
    {
      logger.LogDebug(ex, "{Message}", ex.Message);
    }
  }
}
