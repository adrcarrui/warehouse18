using RFID_API_ver1;
using System;
using System.Collections.Generic;
using System.ComponentModel;

namespace UHFDemo
{

    public class NetPortDB
    {
        private NetPortBindingList _ncList = new NetPortBindingList();
        private Dictionary<string, NetPortDevice> MacIndex = new Dictionary<string, NetPortDevice>();

        public BindingList<NetPortDevice> NetPortList
        {
            get { return _ncList; }
        }
        public void Add(NET_COMM addData)
        {
            string key = null;
            key = addData.DevMac;

            if (!MacIndex.ContainsKey(key))
            {
                NetPortDevice device = new NetPortDevice(addData);
                device.SerialNumber = MacIndex.Count + 1;
                _ncList.Add(device);
                MacIndex.Add(key, device);
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

        public NetPortDevice GetNetPortDeviceByMac(string mac)
        {
            NetPortDevice value = null;
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

        internal void Remove(string devMac)
        {
            if(MacIndex.ContainsKey(devMac))
            {
                _ncList.Remove(MacIndex[devMac]);
                MacIndex.Remove(devMac);
            }
        }
    }

    public class NetPortBindingList : SortableBindingList<NetPortDevice>
    {
        protected override Comparison<NetPortDevice> GetComparer(PropertyDescriptor prop)
        {
            Comparison<NetPortDevice> comparer = null;
            switch (prop.Name)
            {
                case "SerialNumber":
                    comparer = new Comparison<NetPortDevice>(delegate (NetPortDevice a, NetPortDevice b)
                    {
                        return (a.SerialNumber == b.SerialNumber ? 0 : -1); ;
                    });
                    break;
                case "DeviceName":
                    comparer = new Comparison<NetPortDevice>(delegate (NetPortDevice a, NetPortDevice b)
                    {
                        return String.Compare(a.DeviceName, b.DeviceName);
                    });
                    break;
                case "DeviceIp":
                    comparer = new Comparison<NetPortDevice>(delegate (NetPortDevice a, NetPortDevice b)
                    {
                        return String.Compare(a.DeviceIp, b.DeviceIp);
                    });
                    break;
                case "DeviceMac":
                    comparer = new Comparison<NetPortDevice>(delegate (NetPortDevice a, NetPortDevice b)
                    {
                        return String.Compare(a.DeviceMac, b.DeviceMac);
                    });
                    break;
                case "PcMac":
                    comparer = new Comparison<NetPortDevice>(delegate (NetPortDevice a, NetPortDevice b)
                    {
                        return String.Compare(a.PcMac, b.PcMac);
                    });
                    break;
                case "ChipVer":
                    comparer = new Comparison<NetPortDevice>(delegate (NetPortDevice a, NetPortDevice b)
                    {
                        return (a.ChipVer == b.ChipVer ? 0 : -1);
                    });
                    break;
            }
            return comparer;
        }
    }
}
