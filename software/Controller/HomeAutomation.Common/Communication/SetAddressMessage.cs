namespace HomeAutomation.Common.Communication
{
    public class SetAddressMessage : Message
    {
        private ushort _addressToSet;

        public SetAddressMessage(ushort receiverAddress = Protocol.GlobalAddress, ushort senderAddress = Protocol.NoResponseAddress)
            : base(Protocol.MessageType.SetAddress, receiverAddress, senderAddress)
        {
        }

        public ushort AddressToSet
        {
            get => _addressToSet; 
            
            set
            {
                _addressToSet = value;
                InitToRawData();
            }
        }

        protected override void InitToRawData()
        {
            Data = BitConverter.GetBytes(_addressToSet);
        }

        protected override void InitFromRawData()
        {
            var data = Data.ToArray();
            _addressToSet = BitConverter.ToUInt16(data, 0);
        }
    }
}
