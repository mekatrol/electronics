namespace HomeAutomation.Common.Communication
{
    public class FlashDumpPageMessage : Message
    {
        private ushort _pageAddr;

        public FlashDumpPageMessage(ushort receiverAddress = Protocol.GlobalAddress, ushort senderAddress = Protocol.NoResponseAddress)
                            : base(Protocol.MessageType.FlashDumpPage, receiverAddress, senderAddress)
        {
        }

        public ushort PageAddr
        {
            get => _pageAddr;

            set
            {
                _pageAddr = value;
                InitToRawData();
            }
        }

        protected override void InitToRawData()
        {
            Data = BitConverter.GetBytes(PageAddr);
        }
    }
}
