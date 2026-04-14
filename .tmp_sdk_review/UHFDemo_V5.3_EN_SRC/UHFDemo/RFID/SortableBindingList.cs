using System;
using System.ComponentModel;
using System.Collections.Generic;

namespace UHFDemo
{
    public class SortableBindingList<T> : BindingList<T>
    {
        private bool isSorted = false;
        private PropertyDescriptor sortProperty;
        private ListSortDirection sortDirection;
        private bool insideListChangedHandler = false;

        protected override bool IsSortedCore
        {
            get
            {
                return isSorted;
            }
        }

        protected override PropertyDescriptor SortPropertyCore
        {
            get
            {
                return sortProperty;
            }
        }

        protected override ListSortDirection SortDirectionCore
        {
            get
            {
                return sortDirection;
            }
        }

        protected override void ApplySortCore(PropertyDescriptor prop, ListSortDirection direction)
        {
            if (null != prop.PropertyType.GetInterface("IComparable"))
            {
                List<T> itemsList = (List<T>)this.Items;
                Comparison<T> comparer = GetComparer(prop);
                itemsList.Sort(comparer);
                if (direction == ListSortDirection.Descending)
                {
                    itemsList.Reverse();
                }
                isSorted = true;
                sortProperty = prop;
                sortDirection = direction;
                this.OnListChanged(new ListChangedEventArgs(ListChangedType.Reset, -1));
            }
        }

        protected override bool SupportsSortingCore
        {
            get
            {
                return true;
            }
        }

        protected virtual Comparison<T> GetComparer(PropertyDescriptor prop)
        {
            throw new NotImplementedException();
        }

        protected override void RemoveSortCore() { }

        protected override void OnListChanged(ListChangedEventArgs e)
        {
            if (null != SortPropertyCore)
            {
                if (!insideListChangedHandler)
                {
                    insideListChangedHandler = true;
                    ApplySortCore(SortPropertyCore, SortDirectionCore);
                    insideListChangedHandler = false;
                }
            }
            base.OnListChanged(e);
        }
    }
}