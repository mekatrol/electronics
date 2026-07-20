namespace HomeAutomation.Common.Communication
{
    public class InitStorageMessage : Message
    {
        private byte _forceInit;

        public InitStorageMessage(ushort receiverAddress = Protocol.GlobalAddress, ushort senderAddress = Protocol.NoResponseAddress)
            : base(Protocol.MessageType.InitStorage, receiverAddress, senderAddress)
        {
        }

        public byte ForceInit
        {
            get => _forceInit;

            set
            {
                _forceInit = value;
                InitToRawData();
            }
        }

        protected override void InitToRawData()
        {
            Data = new byte[] { _forceInit };
        }

        protected override void InitFromRawData()
        {
            _forceInit = Data[0];
        }
    }
}
