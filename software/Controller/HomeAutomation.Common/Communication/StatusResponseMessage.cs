using System;
using System.Text;

namespace HomeAutomation.Common.Communication
{
    public class StatusResponseMessage : Message
    {
        private string _status = string.Empty;
        private DateTime _dateTime;
        private byte _acFreq;

        public StatusResponseMessage(Message message)
            : base(Protocol.MessageType.GetStatus | Protocol.MessageType.Ok, message)
        {
        }

        public string Status
        {
            get => _status; 
            
            set
            {
                _status = value;
                InitToRawData();
            }
        }

        public DateTime DateTime => _dateTime;

        public int AcFrequency => _acFreq;

        protected override void InitToRawData()
        {
            Data = Encoding.ASCII.GetBytes(_status);
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
            _acFreq = data[13];

            if (!Enum.IsDefined(dotw))
            {
                throw new Exception($"Invalid day of the week value '{dotw}'");
            }

            _dateTime = new DateTime(year, month, day, hour, minute, second, kind);
        }
    }
}
