namespace HomeAutomation.Common.Services.Extensions
{
  public static class HostEnvironment
  {
    public const string HOST_ENVIRONMENT = nameof(HOST_ENVIRONMENT);
    public const string Production = nameof(EnvironmentType.Production);

    public static string EnvironmentName
    {
      get
      {
        return Environment.GetEnvironmentVariable(HOST_ENVIRONMENT) ?? Production;
      }
    }

    /// <summary>
    /// The configured environment type.
    /// </summary>
    public static EnvironmentType EnvironmentType
    {
      get
      {
        if (Enum.TryParse(EnvironmentName, true, out EnvironmentType environmentType))
        {
          return environmentType;
        }

        // Default to production settings.
        return EnvironmentType.Production;
      }
    }
  }
}
