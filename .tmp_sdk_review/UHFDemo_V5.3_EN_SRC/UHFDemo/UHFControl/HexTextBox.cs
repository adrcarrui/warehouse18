using System;
using System.Windows.Forms;
using System.Text.RegularExpressions;

namespace UHFDemo
{
    public class HexTextBox : TextBox
    {
        public HexTextBox()
        {
            InitializeComponent();
        }

        protected override void OnKeyPress(KeyPressEventArgs e)
        {
            string inputStr = e.KeyChar.ToString();
            if (e.KeyChar != (char)ConsoleKey.Backspace)
            {
                if (CheckInput(inputStr) == false)
                {
                    e.Handled = true;
                }
            }
            else
            {
                int nIndex = base.SelectionStart;
                if (nIndex > 0)
                {
                    if (Text[nIndex - 1] == ' ')
                    {
                        string strTemp = Text.Remove(nIndex - 1);
                        Text = strTemp;
                        base.SelectionStart = nIndex - 1;
                    }
                }
            }
            base.OnKeyPress(e);
        }

        private bool CheckInput(string inputString)
        {
            bool flag = false;
            Regex r = new Regex(@"[a-fA-F0-9.\s]+");
            Match m = r.Match(inputString);
            if (m.Success && m.Value == inputString)
            {
                flag = true;
            }
            return flag;
        }

        protected override void OnTextChanged(EventArgs e)
        {
            base.OnTextChanged(e);
            int nIndex = base.SelectionStart;
            if (nIndex > 1)
            {
                if (MaxLength == nIndex)
                {
                    return;
                }
                if (Text[nIndex - 1] != ' ' && Text[nIndex - 2] != ' ')
                {
                    string strSub1 = Text.Substring(0, nIndex);
                    string strSub2 = Text.Substring(nIndex);
                    Text = strSub1 + " " + strSub2;
                    base.SelectionStart = nIndex + 1;
                }
            }
        }

        private void InitializeComponent()
        {
            this.SuspendLayout();
            this.ResumeLayout(false);
        }
    }
}