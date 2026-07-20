using System.IO.Ports;

namespace HomeAutomation.Terminal
{
  internal class Program
  {
    private static SerialPort? _serialPort;
    private static bool _continue;

    static void Main()
    {
      _serialPort = new SerialPort
      {

        // Allow the user to set the appropriate properties.
        PortName = "COM13", 
        BaudRate = 115200,
        Parity = Parity.None,
        DataBits = 8,
        StopBits = StopBits.One,
        Handshake = Handshake.None,
        DtrEnable = false,
        RtsEnable = false,

        // Set the read/write timeouts
        ReadTimeout = 500,
        WriteTimeout = 500
      };

      _serialPort.Open();
      _serialPort.DtrEnable = true;

      _continue = true;
      Thread readThread = new(Read);
      readThread.Start();

      while (true)
      {
        ConsoleKeyInfo key = Console.ReadKey();

        if (key.Key == ConsoleKey.Escape)
        {
          break;
        }

        char[] buffer = { key.KeyChar };
        _serialPort.Write(buffer, 0, 1);
      }

      _continue = false;
      readThread.Join();
      _serialPort.Close();
    }

    public static void Read()
    {
      // Seial port needs to be set before entering background thread
      if (_serialPort == null) return;

      while (_continue)
      {
        try
        {
          var ch = _serialPort!.ReadByte();
          Console.Write((char) ch);
        }
        catch (TimeoutException) { }
        catch (InvalidOperationException ex)
        {
          if (ex.Message.StartsWith("The port is closed."))
          {
            try
            {
              // Try reopening
              _serialPort.Close();
              _serialPort.Open();
            }
            catch
            {
              Thread.Sleep(1000);
            }
            continue;
          }

          Console.WriteLine(ex.ToString());
        }
        catch (Exception ex)
        {
          Console.WriteLine(ex.ToString());
        }
      }
    }
  }
}