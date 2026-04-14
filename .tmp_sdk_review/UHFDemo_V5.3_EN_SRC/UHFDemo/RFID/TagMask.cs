using RFID_API_ver1;
using System.ComponentModel;

namespace UHFDemo
{
    public class TagMask : INotifyPropertyChanged
    {
        protected Select RawRead = null;

        public TagMask(Select addData)
        {
            RawRead = addData;
        }

        public int MaskID { get { return RawRead.MaskID; } }
        public SelectFunction Function { get { return RawRead.Function; } }
        public SessionID Target { get { return RawRead.Target; } }
        public SelectAction Action { get { return RawRead.Action; } }
        public string ActionStr { get { int action = (int)RawRead.Action;
                return action.ToString("x2");
            } }
        public MemBank Bank { get { return RawRead.Bank; } }
        public string StartAddrHexStr { get { return RawRead.StartMaskAddr.ToString("x2"); } }
        public int StartAddr { get { return RawRead.StartMaskAddr; } }
        public string MaskBitLenHexStr { get { return MaskBitLen.ToString("x2"); } }
        public int MaskBitLen { get { return RawRead.MaskBitLen; } }
        public string Mask { get { return RawRead.StrMask; } }
        public int Quantity { get { return RawRead.MaskQuantity; } }
        public int Truncate { get { return RawRead.Truncate; } }

        public void Update(Select mergeData)
        {
            RawRead = mergeData;
            OnPropertyChanged(null);
        }

        #region INotifyPropertyChanged Members

        public event PropertyChangedEventHandler PropertyChanged;

        private void OnPropertyChanged(string name)
        {
            PropertyChangedEventArgs td = new PropertyChangedEventArgs(name);
            try
            {
                if (null != PropertyChanged)
                {
                    PropertyChanged(this, td);
                }
            }
            finally
            {
                td = null;
            }
        }
        #endregion
    }
}