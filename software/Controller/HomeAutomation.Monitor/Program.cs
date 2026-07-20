using HomeAutomation.Common.Services.Extensions;
using Microsoft.Extensions.Logging;
using System.Net.Http.Headers;

namespace HomeAutomation.Monitor
{
  internal class Program
  {
    private static readonly int SLEEP_DELAY = 60000;
    private static ILogger? _logger;
    private static volatile bool _running = true;
    private static readonly CancellationTokenSource _cancellationToken = new();

    static async Task Main(string[] args)
    {
      Services serviceProvider = new();

      try
      {
        _logger = serviceProvider.GetRequiredService<ILogger<Program>>();
        _logger.LogInformation("{app} started [{env}].", nameof(Monitor), HostEnvironment.EnvironmentName);

        Console.CancelKeyPress += new ConsoleCancelEventHandler(ProgramSignalHandler!);

        using HttpClient client = new();
        client.DefaultRequestHeaders.Accept.Clear();
        client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
        client.DefaultRequestHeaders.Add("User-Agent", "Home Automation Monitor");

        var offlineCount = 0;
        var powerCycled = false;
        var noResponseCount = 0;

        while (_running)
        {
          var online = await GetIrrigationOnline(client);

          if (!online)
          {
            offlineCount++;

            if (offlineCount >= 10)
            {
              // If the power has not already been cycled or 
              // there has not been a valid response for more than 10 cycles (10 minutes)
              // then cycle the power
              if (!powerCycled || noResponseCount >= 10)
              {
                await CyclePower(client);
                powerCycled = true;
                noResponseCount = 0;

                // Sleep for 60 seconds
                _cancellationToken.Token.WaitHandle.WaitOne(60000);
              }
              else
              {

                // Reset offline count (as we reached threshold)
                offlineCount = 0;

                noResponseCount++;
              }
            }
          }
          else
          {
            // Reset offline count (as we got a response)
            offlineCount = 0;

            // Reset power cycled flag
            powerCycled = false;

            // Clear no response count
            noResponseCount = 0;
          }

          _logger?.LogInformation("Offline count: {offlineCount}, Power cycled: {powerCycled}, No response count: {noResponseCount}", offlineCount, powerCycled, noResponseCount);

          _cancellationToken.Token.WaitHandle.WaitOne(SLEEP_DELAY);
        }
      }
      catch (Exception ex)
      {
        File.WriteAllText("errordump.log", ex.ToString());
        return;
      }
    }

    static async Task CyclePower(HttpClient client)
    {
      try
      {
        _logger?.LogInformation("Powering off irrigation...");

        // Post power off
        var powerOff = "{ \"relay1\": 0, \"relay2\": 0, \"relay3\": 0, \"relay4\": 0, \"usb\": 0, \"btn\": 0 }";
        var resp = await client.PostAsync("http://pb1.lan/outputs", new StringContent(powerOff));

        if (resp.StatusCode != System.Net.HttpStatusCode.OK)
        {
          _logger?.LogInformation("{resp}", resp.ToString());
        }

        _cancellationToken.Token.WaitHandle.WaitOne(60000);

        _logger?.LogInformation("Powering on irrigation...");

        // Post power on
        var powerOn = "{ \"relay1\": 1, \"relay2\": 0, \"relay3\": 0, \"relay4\": 0, \"usb\": 0, \"btn\": 0 }";

        resp = await client.PostAsync("http://pb1.lan/outputs", new StringContent(powerOn));

        if (resp.StatusCode != System.Net.HttpStatusCode.OK)
        {
          _logger?.LogInformation("{resp}", resp.ToString());
        }
      }
      catch (Exception ex)
      {
        _logger?.LogError(ex);
      }
    }

    static async Task<bool> GetIrrigationOnline(HttpClient client)
    {
      try
      {
        // Get JSON response
        var _ = await client.GetStringAsync("http://g.lan/jc?pw=a6d82bced638de3def1e9bbb4983225c");

        // No exception then irrigation is online
        return true;
      }
      catch (Exception /* ex */)
      {
        //_logger.LogInformation(ex.ToString());

        // Exception occured so irrigation is probably offline
        return false;
      }
    }

    protected static void ProgramSignalHandler(object sender, ConsoleCancelEventArgs args)
    {
      _logger?.LogInformation("{app} stopping by '{specialKey}'.", nameof(Monitor), args.SpecialKey);
      _cancellationToken?.Cancel();
      _running = false;

      // Cancel the operation and we will clean up via normal exit process
      args.Cancel = true;
    }
  }
}