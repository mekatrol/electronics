namespace HomeAutomation.Common.Communication
{
    public class SetDateTimeMessage : Message
    {
        private DateTime _dateTime = DateTime.UtcNow;

        /// <summary>
        /// Construct a set time message. Addresses default to global address for reciever (all recievers)
        /// and no response address for receiver (no acks required from receiver)
        /// </summary>
        public SetDateTimeMessage(ushort receiverAddress = Protocol.GlobalAddress, ushort senderAddress = Protocol.NoResponseAddress)
            : base(Protocol.MessageType.SetDateTime, receiverAddress, senderAddress)
        {
        }

        public SetDateTimeMessage(Message copyFromMessage) : base(Protocol.MessageType.SetDateTime, copyFromMessage)
        {
        }

        public DateTime DateTime
        {
            get => _dateTime;

            set
            {
                _dateTime = value;
                InitToRawData();
            }
        }

        protected override void InitToRawData()
        {
            var data = new List<byte>();

            data.AddRange(BitConverter.GetBytes((short)_dateTime.Year));
            data.AddRange(BitConverter.GetBytes((short)_dateTime.Month));
            data.AddRange(BitConverter.GetBytes((short)_dateTime.Day));
            data.AddRange(BitConverter.GetBytes((short)_dateTime.Hour));
            data.AddRange(BitConverter.GetBytes((short)_dateTime.Minute));
            data.AddRange(BitConverter.GetBytes((short)_dateTime.Second));

            // Last byte:
            //  top nibble is the day of the week
            //  lower nibble is date time kind
            data.Add((byte)((byte)_dateTime.DayOfWeek << 4 | (byte)_dateTime.Kind & 0x0F));

            // Set base class data field
            Data = data;
        }

        protected override void InitFromRawData()
        {
            var data = Data.ToArray();
            var year = BitConverter.ToUInt16(data, 0);
            var month = BitConverter.ToUInt16(data, 2);
            var day = BitConverter.ToUInt16(data, 4);
            var hour = BitConverter.ToUInt16(data, 6);
            var minute = BitConverter.ToUInt16(data, 8);
            var second = BitConverter.ToUInt16(data, 10);
            var dotw = (DayOfWeek)(data[12] >> 4);
            var kind = (DateTimeKind)(data[12] & 0xF);

            if (!Enum.IsDefined(dotw))
            {
                throw new Exception($"Invalid day of the week value '{dotw}'");
            }

            _dateTime = new DateTime(year, month, day, hour, minute, second, kind);
        }
    }
}
