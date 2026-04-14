using RFID_API_ver1;
using System;
using System.Collections.Generic;
using System.ComponentModel;

namespace UHFDemo
{
    public class NetCardDB
    {
        private NetCardBindingList _ncList = new NetCardBindingList();
        private Dictionary<string, NetCard> MacIndex = new Dictionary<string, NetCard>();

        public BindingList<NetCard> NetCardList
        {
            get { return _ncList; }
        }
        public void Add(NetCard addData)
        {
            string key = null;
            key = addData.Mac;

            if (!MacIndex.ContainsKey(key))
            {
                addData.SerialNumber = MacIndex.Count + 1;
                _ncList.Add(addData);
                MacIndex.Add(key, addData);
            }
            else
            {
                MacIndex[key].Update(addData);
            }
        }

        public void Clear()
        {
            _ncList.Clear();
            MacIndex.Clear();
        }

        public NetCard GetNetCardByMac(string mac)
        {
            NetCard value = null;
            if (MacIndex.TryGetValue(mac, out value))
            {
                return value;
            }
            else
            {
                return null;
            }
        }

        public int GetCount()
        {
            return _ncList.Count;
        }
    }

    public class NetCardBindingList : SortableBindingList<NetCard>
    {
        protected override Comparison<NetCard> GetComparer(PropertyDescriptor prop)
        {
            Comparison<NetCard> comparer = null;
            switch (prop.Name)
            {
                case "SerialNumber":
                    comparer = new Comparison<NetCard>(delegate (NetCard a, NetCard b)
                    {
                        return (a.SerialNumber == b.SerialNumber ? 0 : -1); ;
                    });
                    break;
                case "Description":
                    comparer = new Comparison<NetCard>(delegate (NetCard a, NetCard b)
                    {
                        return String.Compare(a.Description, b.Description);
                    });
                    break;
                case "Ip":
                    comparer = new Comparison<NetCard>(delegate (NetCard a, NetCard b)
                    {
                        return String.Compare(a.Ip, b.Ip);
                    });
                    break;
                case "Mask":
                    comparer = new Comparison<NetCard>(delegate (NetCard a, NetCard b)
                    {
                        return String.Compare(a.Mask, b.Mask);
                    });
                    break;
                case "Mac":
                    comparer = new Comparison<NetCard>(delegate (NetCard a, NetCard b)
                    {
                        return String.Compare(a.Mac, b.Mac);
                    });
                    break;
            }
            return comparer;
        }
    }
}