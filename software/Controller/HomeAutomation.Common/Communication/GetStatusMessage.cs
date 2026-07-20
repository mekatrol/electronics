using System.Text;

namespace HomeAutomation.Common.Communication
{
    public class GetStatusMessage : Message
    {
        private string _status = string.Empty;

        public GetStatusMessage(ushort receiverAddress = Protocol.GlobalAddress, ushort senderAddress = Protocol.NoResponseAddress)
            : base(Protocol.MessageType.GetStatus, receiverAddress, senderAddress)
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

        protected override void InitToRawData()
        {
            Data = Encoding.ASCII.GetBytes(_status);
        }

        protected override void InitFromRawData()
        {
            var data = Data.ToArray();
            _status = Encoding.ASCII.GetString(data);
        }
    }
}
