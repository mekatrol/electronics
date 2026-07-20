using HomeAutomation.Common.Communication;
using System.IO.Ports;
using System.Text;
using static HomeAutomation.Common.Communication.Protocol;

namespace HomeAutomation.ControllerCLI
{
    internal class Program
    {
        private static readonly StringComparer _stringComparer = StringComparer.OrdinalIgnoreCase;
        private static readonly ushort _controllerAddress = 100;
        private static readonly ushort _deviceAddress = 1;

        private static bool _continue;
        private static SerialPort? _serialPort;

        private static readonly MessageQueue _queuedSendMessages = new();

        static void Main()
        {
            Thread readThread = new(Read);

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
            readThread.Start();

            Console.WriteLine("Type QUIT to exit");

            string? input;
            while (_continue)
            {
                input = Console.ReadLine()?.Trim();

                // If not command then continue
                if (string.IsNullOrWhiteSpace(input)) continue;

                if (_stringComparer.Equals("quit", input))
                {
                    _continue = false;
                    break;
                }

                if (_stringComparer.Equals("addr", input))
                {
                    Console.WriteLine($"Setting device address to '{_deviceAddress}'");
                    var message = new SetAddressMessage(senderAddress: _controllerAddress)
                    {
                        AddressToSet = _deviceAddress
                    };

                    _queuedSendMessages.QueueMessage(message, MessageType.Ok | message.MessageType,
                    TimeSpan.FromSeconds(3),
                    (sentMessage, responseMessage) =>
                    {
                        if (responseMessage == null)
                        {
                            Console.WriteLine("Message timed out");
                        }
                        else
                        {
                            if ((responseMessage.MessageType & MessageType.Ok) != 0)
                            {
                                Console.WriteLine("Setting device address succeeded");
                            }
                        }
                    });
                    continue;
                }

                if (_stringComparer.Equals("time", input))
                {
                    Console.WriteLine("Setting device time");
                    var message = new SetDateTimeMessage(senderAddress: _controllerAddress)
                    {
                        DateTime = DateTime.Now
                    };

                    Action<Message, Message?>? responseCallback = null;

                    if (message.ReceiverAddress != GlobalAddress)
                    {
                        responseCallback = (sentMessage, responseMessage) =>
                        {
                            if (responseMessage == null)
                            {
                                Console.WriteLine("Message timed out");
                            }
                            else
                            {
                                if ((responseMessage.MessageType & MessageType.Ok) != 0)
                                {
                                    Console.WriteLine("Setting device time succeeded");
                                }
                            }
                        };
                    }

                    // Queue message, sent to all devices no no handler required
                    _queuedSendMessages.QueueMessage(message, MessageType.Ok | message.MessageType, TimeSpan.FromSeconds(3), responseCallback);
                    continue;
                }

                if (_stringComparer.Equals("status", input))
                {
                    Console.WriteLine("Getting device status");
                    var message = new GetStatusMessage(receiverAddress: _deviceAddress, senderAddress: _controllerAddress);

                    _queuedSendMessages.QueueMessage(message, MessageType.Ok | message.MessageType,
                    TimeSpan.FromSeconds(3),
                    (sentMessage, responseMessage) =>
                    {
                        if (responseMessage == null)
                        {
                            Console.WriteLine("Message timed out");
                        }
                        else
                        {
                            var statusMessage = new StatusResponseMessage(responseMessage);
                            Console.WriteLine($"Device date time {statusMessage.DateTime}");
                            Console.WriteLine($"Device AC Frequency {statusMessage.AcFrequency}");
                        }
                    });
                    continue;
                }

                var parts = input.Split(new char[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);

                if (_stringComparer.Equals("flash", parts[0]))
                {
                    if (parts.Length == 1)
                    {
                        Console.WriteLine("Flash command missing sub-command");
                        return;
                    }

                    var subCommand = parts[1];
                    Message? message = null;

                    if (_stringComparer.Equals("dump", subCommand))
                    {
                        if (parts.Length != 3)
                        {
                            Console.WriteLine($"flash dump invalid parameter count '{input}', expecting flash dump command followed by flash page number");
                            return;
                        }

                        if (!ushort.TryParse(parts[1], out ushort pageAddr))
                        {
                            Console.WriteLine($"flash dump invalid page number: {parts[1]}");
                            return;
                        }

                        if (pageAddr < 0 || pageAddr > 65535)
                        {
                            Console.WriteLine("flash dump page number should be in rage 0 to 65535");
                            return;
                        }

                        Console.WriteLine("Dumping flash page");
                        message = new FlashDumpPageMessage(receiverAddress: _deviceAddress, senderAddress: _controllerAddress)
                        {
                            PageAddr = pageAddr
                        };
                    }
                    else if (_stringComparer.Equals("reset", subCommand))
                    {
                        if (parts.Length != 2)
                        {
                            Console.WriteLine($"flash reset invalid parameter count '{input}', expecting flash reset command without any parameters");
                            return;
                        }

                        message = new FlashResetMessage(receiverAddress: _deviceAddress, senderAddress: _controllerAddress);
                    }
                    else
                    {
                        Console.WriteLine($"flash invalid sub command '{subCommand}'");
                        return;
                    }

                    _queuedSendMessages.QueueMessage(message, MessageType.Ok | message.MessageType,
                    TimeSpan.FromSeconds(3),
                    (sentMessage, responseMessage) =>
                    {
                        if (responseMessage == null)
                        {
                            Console.WriteLine("Message timed out");
                        }
                    });
                    continue;
                }

                if (_stringComparer.Equals("storage", parts[0]))
                {
                    if (parts.Length == 1)
                    {
                        Console.WriteLine("Storage command needs acion to perform, eg storage init");
                        continue;
                    }

                    if (_stringComparer.Equals("init", parts[1]))
                    {
                        byte forceInit = 0x00;
                        if (parts.Length > 2)
                        {
                            if (!bool.TryParse(parts[2], out bool forceInitBool))
                            {
                                if (!byte.TryParse(parts[2], out forceInit))
                                {
                                    Console.WriteLine("Storage init command force flag not a valid boolean or byte value");
                                    continue;
                                }
                            }
                            else
                            {
                                forceInit = forceInitBool ? (byte)0x1 : (byte)0x0;
                            }
                        }

                        Console.WriteLine("Initialising storage");
                        var message = new InitStorageMessage(senderAddress: _controllerAddress)
                        {
                            ForceInit = forceInit
                        };

                        _queuedSendMessages.QueueMessage(message, MessageType.Ok | message.MessageType,
                        TimeSpan.FromSeconds(3),
                        (sentMessage, responseMessage) =>
                        {
                            if (responseMessage == null)
                            {
                                Console.WriteLine("Message timed out");
                            }
                            else
                            {
                                Console.WriteLine(responseMessage);
                            }
                        });

                        continue;
                    }

                    Console.WriteLine($"Storage command unknown action '{parts[1]}'");
                    continue;
                }

                Console.WriteLine($"Unknown command '{parts[0]}'");
            }

            readThread.Join();
            _serialPort.Close();
        }

        public static void Read()
        {
            var rxBuffer = new byte[2048];
            var rxIndex = 0;

            // Seial port needs to be set before entering background thread
            if (_serialPort == null) return;

            while (_continue)
            {
                try
                {
                    // Any queued messages?
                    if (_queuedSendMessages.TryGetAndMarkSent(out MessageQueueItem? item) && item != null)
                    {
                        // Send the message
                        var asciiMessage = item.MessageToSend.Build();
                        _serialPort.Write(asciiMessage);

                        if (item.Handler == null)
                        {
                            // If there is no handler then remove from queue
                            // (we are not waiting for a response)
                            _queuedSendMessages.TryRemove(item.Id);
                        }
                    }

                    // Any expired messages?
                    while (_queuedSendMessages.TryGetExpired(out item) && item != null)
                    {
                        // Timed out
                        item.Handler?.Invoke(item.MessageToSend, null);
                    }

                    var ch = _serialPort!.ReadByte();

                    if (ch == Som)
                    {
                        // SOM only ever occurs at begining of message so reset 
                        // the receive index
                        rxIndex = 0;
                    }
                    else if (rxIndex == 0)
                    {
                        // Need SOM to start
                        continue;
                    }

                    rxBuffer[rxIndex++] = (byte)ch;

                    if (ch == Eom)
                    {
                        try
                        {
                            var asciiMessage = Encoding.UTF8.GetString(rxBuffer, 0, rxIndex);
                            var message = Message.FromData(asciiMessage);

                            var sentMessageType = (MessageType)((ushort)message.MessageType & ~(ushort)MessageType.Ok);
                            if (_queuedSendMessages.TryGetById(MessageQueue.GenerateId(sentMessageType, message.ReceiverAddress, message.SenderAddress), out item))
                            {
                                item?.Handler?.Invoke(item.MessageToSend, message);
                            }
                        }
                        catch (Exception ex)
                        {
                            Console.WriteLine(ex.ToString());
                        }
                    }

                    if (rxIndex == rxBuffer.Length)
                    {
                        // Reset buffer (buffer overflow)
                        rxIndex = 0;
                    }
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