using System;
using System.Net;
using System.Drawing;
using System.Windows.Forms;
using System.ComponentModel;
using System.Text.RegularExpressions;

namespace UHFDemo
{
    public class IpAddressTextBox : UserControl
    {
        private IContainer components = null;
        private Panel pnlMain;
        private Label lbldot1;
        private Label lbldot2;
        private Label lbldot3;
        private TextBox Ip1;
        private TextBox Ip2;
        private TextBox Ip3;
        private TextBox Ip4;
        private string IpAddress;

        public IpAddressTextBox()
        {
            InitializeComponent();
        }

        public string IpAddressStr
        {
            get
            {
                string Ipstr = Ip1.Text + "." + Ip2.Text + "." + Ip3.Text + "." + Ip4.Text;
                try
                {
                    IPAddress.Parse(Ipstr);
                }
                catch
                {
                    return "";
                }
                this.IpAddress = Ipstr;
                return this.IpAddress;
            }
            set
            {
                string ipStr = value;
                if (string.IsNullOrEmpty(ipStr))
                {
                    Ip1.Text = "";
                    Ip2.Text = "";
                    Ip3.Text = "";
                    Ip4.Text = "";
                    IpAddress = "";
                }
                else
                {
                    try
                    {
                        IPAddress ipValue = IPAddress.Parse(ipStr);
                        string[] ips = ipStr.Split('.');
                        Ip1.Text = ips[0];
                        Ip2.Text = ips[1];
                        Ip3.Text = ips[2];
                        Ip4.Text = ips[3];
                        IpAddress = ipStr;
                    }
                    catch
                    {
                        Ip1.Text = "";
                        Ip2.Text = "";
                        Ip3.Text = "";
                        Ip4.Text = "";
                        IpAddress = "";
                    }
                }
            }
        }

        private void Ip1_TextChanged(object sender, EventArgs e)
        {
            if (Ip1.Text.Length == 3 && Ip1.Text.Length > 0 && Ip1.SelectionLength == 0)
            {
                if (Convert.ToInt32(Ip1.Text) > 223)
                {
                    Ip1.Text = "223";
                }
                else if (Convert.ToInt32(Ip1.Text) < 1)
                {
                    Ip1.Text = "1";
                }
                else
                {
                    Ip2.Focus();
                    Ip2.Select(0, Ip2.Text.Length);
                }
            }
        }

        private void Ip2_TextChanged(object sender, EventArgs e)
        {
            if (Ip2.Text.Length == 3 && Ip2.Text.Length > 0 && Ip2.SelectionLength == 0)
            {
                if (Convert.ToInt32(Ip2.Text) > 255)
                {
                    Ip2.Text = "255";
                }
                else
                {
                    Ip3.Focus();
                    Ip3.Select(0, Ip3.Text.Length);
                }
            }
        }

        private void Ip3_TextChanged(object sender, EventArgs e)
        {
            if (Ip3.Text.Length == 3 && Ip3.Text.Length > 0 && Ip3.SelectionLength == 0)
            {
                if (Convert.ToInt32(Ip3.Text) > 255)
                {
                    Ip3.Text = "255";
                }
                else
                {
                    Ip4.Focus();
                    Ip4.Select(0, Ip4.Text.Length);
                }
            }
        }

        private void Ip4_TextChanged(object sender, EventArgs e)
        {
            if (Ip4.Text.Length == 3 && Ip4.Text.Length > 0 && Ip4.SelectionLength == 0)
            {
                if (Convert.ToInt32(Ip4.Text) > 255)
                {
                    Ip4.Text = "255";
                }
            }
        }

        private bool CheckInput(string inputString)
        {
            bool flag = false;
            Regex r = new Regex(@"[0-9\s]+");
            Match m = r.Match(inputString);
            if (m.Success && m.Value == inputString)
            {
                flag = true;
            }
            return flag;
        }

        private void Ip1_KeyPress(object sender, KeyPressEventArgs e)
        {
            string inputStr = e.KeyChar.ToString();
            if (e.KeyChar != (char)ConsoleKey.Backspace)
            {
                if (e.KeyChar == 46 && Ip1.Text.Length > 0 && Ip1.SelectionLength == 0)
                {
                    Ip2.Focus();
                    Ip2.Select(0, Ip2.Text.Length);
                }
                if (CheckInput(inputStr) == false)
                {
                    e.Handled = true;
                }
            }
            base.OnKeyPress(e);
        }

        private void Ip2_KeyPress(object sender, KeyPressEventArgs e)
        {
            string inputStr = e.KeyChar.ToString();
            if (e.KeyChar != (char)ConsoleKey.Backspace)
            {
                if (e.KeyChar == 46 && Ip2.Text.Length > 0 && Ip2.SelectionLength == 0)
                {
                    Ip3.Focus();
                    Ip3.Select(0, Ip3.Text.Length);
                }
                if (CheckInput(inputStr) == false)
                {
                    e.Handled = true;
                }
            }
            base.OnKeyPress(e);
        }

        private void Ip3_KeyPress(object sender, KeyPressEventArgs e)
        {
            string inputStr = e.KeyChar.ToString();
            if (e.KeyChar != (char)ConsoleKey.Backspace)
            {
                if (e.KeyChar == 46 && Ip3.Text.Length > 0 && Ip3.SelectionLength == 0)
                {
                    Ip4.Focus();
                    Ip4.Select(0, Ip4.Text.Length);
                }
                if (CheckInput(inputStr) == false)
                {
                    e.Handled = true;
                }
            }
            base.OnKeyPress(e);
        }

        private void Ip4_KeyPress(object sender, KeyPressEventArgs e)
        {
            string inputStr = e.KeyChar.ToString();
            if (e.KeyChar != (char)ConsoleKey.Backspace)
            {
                if (CheckInput(inputStr) == false)
                {
                    e.Handled = true;
                }
            }
            base.OnKeyPress(e);
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        private void InitializeComponent()
        {
            this.pnlMain = new Panel();
            this.lbldot1 = new Label();
            this.lbldot2 = new Label();
            this.lbldot3 = new Label();
            this.Ip1 = new TextBox();
            this.Ip2 = new TextBox();
            this.Ip3 = new TextBox();
            this.Ip4 = new TextBox();
            this.pnlMain.SuspendLayout();
            this.SuspendLayout();
            // 
            // pnlMain
            // 
            this.pnlMain.BackColor = Color.White;
            this.pnlMain.BorderStyle = BorderStyle.Fixed3D;
            this.pnlMain.Controls.Add(this.lbldot1);
            this.pnlMain.Controls.Add(this.lbldot2);
            this.pnlMain.Controls.Add(this.lbldot3);
            this.pnlMain.Controls.Add(this.Ip1);
            this.pnlMain.Controls.Add(this.Ip2);
            this.pnlMain.Controls.Add(this.Ip3);
            this.pnlMain.Controls.Add(this.Ip4);
            this.pnlMain.Dock = DockStyle.Fill;
            this.pnlMain.Location = new Point(0, 0);
            this.pnlMain.Name = "pnlMain";
            this.pnlMain.Size = new Size(121, 21);
            this.pnlMain.TabIndex = 1;
            // 
            // lbldot1
            // 
            this.lbldot1.AutoSize = true;
            this.lbldot1.Location = new Point(22, 4);
            this.lbldot1.Name = "lbldot1";
            this.lbldot1.Size = new Size(11, 12);
            this.lbldot1.TabIndex = 1;
            this.lbldot1.Text = ".";
            // 
            // lbldot2
            // 
            this.lbldot2.AutoSize = true;
            this.lbldot2.Location = new Point(51, 4);
            this.lbldot2.Name = "lbldot2";
            this.lbldot2.Size = new Size(11, 12);
            this.lbldot2.TabIndex = 5;
            this.lbldot2.Text = ".";
            // 
            // lbldot3
            // 
            this.lbldot3.AutoSize = true;
            this.lbldot3.Location = new Point(83, 4);
            this.lbldot3.Name = "lbldot3";
            this.lbldot3.Size = new Size(11, 12);
            this.lbldot3.TabIndex = 6;
            this.lbldot3.Text = ".";
            // 
            // Ip1
            // 
            this.Ip1.BorderStyle = BorderStyle.None;
            this.Ip1.Location = new Point(0, 1);
            this.Ip1.MaxLength = 3;
            this.Ip1.Name = "Ip1";
            this.Ip1.ShortcutsEnabled = false;
            this.Ip1.Size = new Size(20, 14);
            this.Ip1.TabIndex = 0;
            this.Ip1.TextAlign = HorizontalAlignment.Center;
            this.Ip1.TextChanged += new EventHandler(this.Ip1_TextChanged);
            this.Ip1.KeyPress += new KeyPressEventHandler(this.Ip1_KeyPress);
            // 
            // Ip2
            // 
            this.Ip2.BorderStyle = BorderStyle.None;
            this.Ip2.Location = new Point(33, 1);
            this.Ip2.MaxLength = 3;
            this.Ip2.Name = "Ip2";
            this.Ip2.ShortcutsEnabled = false;
            this.Ip2.Size = new Size(20, 14);
            this.Ip2.TabIndex = 1;
            this.Ip2.TextAlign = HorizontalAlignment.Center;
            this.Ip2.TextChanged += new EventHandler(this.Ip2_TextChanged);
            this.Ip2.KeyPress += new KeyPressEventHandler(this.Ip2_KeyPress);
            // 
            // Ip3
            // 
            this.Ip3.BorderStyle = BorderStyle.None;
            this.Ip3.Location = new Point(62, 1);
            this.Ip3.MaxLength = 3;
            this.Ip3.Name = "Ip3";
            this.Ip3.ShortcutsEnabled = false;
            this.Ip3.Size = new Size(20, 14);
            this.Ip3.TabIndex = 2;
            this.Ip3.TextAlign = HorizontalAlignment.Center;
            this.Ip3.TextChanged += new EventHandler(this.Ip3_TextChanged);
            this.Ip3.KeyPress += new KeyPressEventHandler(this.Ip3_KeyPress);
            // 
            // Ip4
            // 
            this.Ip4.BorderStyle = BorderStyle.None;
            this.Ip4.Location = new Point(94, 1);
            this.Ip4.MaxLength = 3;
            this.Ip4.Name = "Ip4";
            this.Ip4.ShortcutsEnabled = false;
            this.Ip4.Size = new Size(20, 14);
            this.Ip4.TabIndex = 3;
            this.Ip4.TextAlign = HorizontalAlignment.Center;
            this.Ip4.TextChanged += new EventHandler(this.Ip4_TextChanged);
            this.Ip4.KeyPress += new KeyPressEventHandler(this.Ip4_KeyPress);
            // 
            // IpAddressTextBox
            // 
            this.AutoScaleDimensions = new SizeF(6F, 12F);
            this.AutoScaleMode = AutoScaleMode.Font;
            this.Controls.Add(this.pnlMain);
            this.Name = "IpAddressTextBox";
            this.Size = new Size(121, 21);
            this.pnlMain.ResumeLayout(false);
            this.pnlMain.PerformLayout();
            this.ResumeLayout(false);
        }
    }
}