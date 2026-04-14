using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace UHFDemo
{
    public partial class FactoryReset : Form
    {
        public FactoryReset()
        {
            InitializeComponent();
        }

        private void btnFreqSure_Click(object sender, EventArgs e)
        {
            if (rbEurFreq.Checked)
            {
                UHFDemo.FreqValue = 1;
            }

            if(rbUSFreq.Checked)
            {
                UHFDemo.FreqValue = 2;
            }

            this.DialogResult = DialogResult.OK;
            this.Close();
        }

        private void btnFreqCancle_Click(object sender, EventArgs e)
        {
            this.DialogResult = DialogResult.Cancel;
            this.Close();
        }
    }
}
