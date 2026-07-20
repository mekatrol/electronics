namespace HomeAutomation.Common.Configuration
{
  public class ApiDevice
  {
    public string Name { get; set; } = "";
    public string Url { get; set; } = "";
    public string UserName { get; set; } = "";
    public string Password { get; set; } = "";
  }

  public class ApiDevices : List<ApiDevice> { }
}
