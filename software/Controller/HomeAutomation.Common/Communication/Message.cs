namespace HomeAutomation.Common.Communication
{
    public class Message
    {
        public Message(Protocol.MessageType messageType, ushort receiverAddress, ushort senderAddress)
        {
            MessageType = messageType;
            ReceiverAddress = receiverAddress;
            SenderAddress = senderAddress;
            Data = new List<byte>();

            // Initialise derived class data from raw data
            InitToRawData();
        }

        protected Message(Protocol.MessageType messageType, Message copyFromMessage)
        {
            if (copyFromMessage.MessageType != messageType)
            {
                throw new InvalidOperationException($"Message type '{copyFromMessage.MessageType}', expected '{messageType}");
            }

            ReceiverAddress = copyFromMessage.ReceiverAddress;
            SenderAddress = copyFromMessage.SenderAddress;
            MessageType = messageType;
            Data = copyFromMessage.Data;

            // Initialise derived class data from raw data
            InitFromRawData();
        }

        public Protocol.MessageType MessageType { get; }

        public ushort ReceiverAddress { get; set; }

        public ushort SenderAddress { get; set; }

        protected IList<byte> Data { get; set; }

        public virtual string Build()
        {
            var message = new List<byte>();

            // Add receiver address (ushort)
            message.AddRange(BitConverter.GetBytes(ReceiverAddress));

            // Add sender length (ushort)
            message.AddRange(BitConverter.GetBytes(SenderAddress));

            // Add message type (ushort)
            message.AddRange(BitConverter.GetBytes((ushort)MessageType));

            // Add message length not including SOM, EOM and CRC (ushort)
            message.AddRange(BitConverter.GetBytes((ushort)(
                message.Count +  // Message length so far
                sizeof(ushort) + // Length length
                Data.Count)));   // Data length

            if (Data.Count > 0)
            {
                message.AddRange(Data);
            }

            // Calculate the CRC
            var crc = Crc16.CalcBufferCrc(message);

            // Add CRC
            message.AddRange(BitConverter.GetBytes(crc));

            return $"{Protocol.Som}{string.Join("", message.Select(x => $"{(byte)(x >> 4):X}{(byte)(x & 0x0F):X}"))}{Protocol.Eom}";
        }

        /// <summary>
        /// Allows a derived class to initialise its internal state from the raw data
        /// </summary>
        protected virtual void InitFromRawData() { }

        /// <summary>
        /// Allows a derived class to initialise the data from its internal state
        /// </summary>
        protected virtual void InitToRawData() { }

        public override string ToString()
        {
            return $"{ReceiverAddress:4X}{SenderAddress:X4}{MessageType}{Data.Count}";
        }

        public static Message FromData(string asciiData)
        {
            // ASCII data must be a multiple of 2
            if (asciiData.Length % 2 != 0) throw new Exception("ASCII message length must be a multiple of 2");

            if (asciiData.Length < 22)
            {
                // 22 is the minimum valid length for an ASCII message
                // SOM (1) + RCV ADDR (4) + SND ADDR (4) + MT (4) + LEN (4) + CRC (4) + EOM (1)
                throw new Exception($"ASCII message must be at least 22 characters long, ASCII message was {asciiData.Length} long.");
            }

            if (asciiData[0] != Protocol.Som) throw new Exception("SOM not found");
            if (asciiData[^1] != Protocol.Eom) throw new Exception("EOM not found");

            // Strip SOM and EOM from ascii data
            asciiData = asciiData[1..^1];

            var binaryData = AsciiToBinary(asciiData);

            // Calculate CRC on binary
            var messageWithoutCrc = binaryData[..^2];
            ushort calculatedCrc = Crc16.CalcBufferCrc(messageWithoutCrc);

            var messageCrc = BitConverter.ToUInt16(binaryData, binaryData.Length - 2);

            if (calculatedCrc != messageCrc)
            {
                throw new Exception($"Invalid CRC '{messageCrc}', expecting '{calculatedCrc}'");
            }

            var messageType = (Protocol.MessageType)BitConverter.ToUInt16(binaryData, 4);
            var message = new Message(
                messageType, 
                BitConverter.ToUInt16(binaryData, 0), // Receiver address 
                BitConverter.ToUInt16(binaryData, 2)) // Sender address
            {
                Data = binaryData[8..^2] // Skip rcv addr, sndr addr, data length (begining) and CRC (end)
            };

            var dataLength = BitConverter.ToUInt16(messageWithoutCrc, 6);

            if (dataLength != message.Data.Count)
            {
                throw new Exception($"Invalid data length '{dataLength}', expecting '{message.Data.Count}'");
            }

            return message;
        }

        private static byte[] AsciiToBinary(string asciiData)
        {
            // Binary data length is half ascii data length
            byte[] binaryData = new byte[asciiData.Length / 2];

            for (int i = 0; i < asciiData.Length; i += 2)
            {
                char ch1 = asciiData[i];
                char ch2 = asciiData[i + 1];
                binaryData[i >> 1] = (byte)(AsciiToByte(ch1) << 4 | AsciiToByte(ch2));
            }

            return binaryData;
        }

        private static byte AsciiToByte(char ch)
        {
            // Convert ASCII chracter to binary equiv
            // [0-9] = [48 -  57] = [0x30 - 0x39]
            // [A-Z] = [65 -  90] = [0x41 - 0x5A]
            // [a-z] = [97 - 122] = [0x61 - 0x7A]

            // a - z are largest values
            if (ch > 'Z')
            {
                return (byte)(ch - 'a' + 10);
            }

            // A - Z are next largest
            if (ch > '9')
            {
                return (byte)(ch - 'A' + 10);
            }

            // Leaves 0 - 9
            return (byte)(ch - '0');
        }
    }
}
