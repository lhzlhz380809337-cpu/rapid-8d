using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Reflection;
using System.Windows.Forms;

[assembly: AssemblyTitle("启动 Rapid 8D")]
[assembly: AssemblyProduct("Rapid 8D")]
[assembly: AssemblyVersion("0.3.0.0")]
[assembly: AssemblyFileVersion("0.3.0.0")]

internal sealed class LaunchSplash : Form
{
    private readonly string target;
    private readonly ProgressBar progress = new ProgressBar();

    internal LaunchSplash(string executable)
    {
        target = executable;
        ClientSize = new Size(560, 318);
        StartPosition = FormStartPosition.CenterScreen;
        FormBorderStyle = FormBorderStyle.None;
        BackColor = Color.FromArgb(18, 51, 74);
        ShowInTaskbar = true;
        TopMost = true;

        var edge = new Panel { Dock = DockStyle.Fill, Padding = new Padding(1), BackColor = Color.FromArgb(48, 136, 140) };
        var surface = new Panel { Dock = DockStyle.Fill, BackColor = Color.FromArgb(18, 51, 74) };
        edge.Controls.Add(surface);

        var mark = new Label {
            Text = "8D", TextAlign = ContentAlignment.MiddleCenter, Location = new Point(43, 43), Size = new Size(54, 54),
            Font = new Font("Georgia", 17, FontStyle.Bold), ForeColor = Color.White,
            BackColor = Color.FromArgb(17, 125, 131)
        };
        var name = new Label {
            Text = "Rapid 8D", AutoSize = true, Location = new Point(119, 42),
            Font = new Font("Microsoft YaHei UI", 26, FontStyle.Bold), ForeColor = Color.White
        };
        var subtitle = new Label {
            Text = "质量问题研析工作台", AutoSize = true, Location = new Point(122, 87),
            Font = new Font("Microsoft YaHei UI", 10), ForeColor = Color.FromArgb(174, 203, 211)
        };
        var rule = new Panel { Location = new Point(44, 130), Size = new Size(472, 1), BackColor = Color.FromArgb(47, 85, 103) };
        var message = new Label {
            Text = "正在载入研析工作区…", AutoSize = true, Location = new Point(44, 163),
            Font = new Font("Microsoft YaHei UI", 10), ForeColor = Color.FromArgb(210, 228, 233)
        };
        progress.Location = new Point(44, 200);
        progress.Size = new Size(472, 5);
        progress.Style = ProgressBarStyle.Marquee;
        progress.MarqueeAnimationSpeed = 26;
        var method = new Label {
            Text = "FACTS  ·  EVIDENCE  ·  VERIFICATION  ·  PREVENTION", AutoSize = true, Location = new Point(44, 221),
            Font = new Font("Segoe UI", 7), ForeColor = Color.FromArgb(92, 169, 172)
        };
        var credit = new Label {
            Text = "BUILT & CURATED BY 刘鸿志   ·   v0.3.0", AutoSize = true, Location = new Point(44, 273),
            Font = new Font("Microsoft YaHei UI", 8), ForeColor = Color.FromArgb(120, 155, 166)
        };
        surface.Controls.AddRange(new Control[] { mark, name, subtitle, rule, message, progress, method, credit });
        Controls.Add(edge);

        Shown += delegate {
            BeginInvoke(new Action(StartApplication));
        };
    }

    private void StartApplication()
    {
        try
        {
            Process.Start(new ProcessStartInfo {
                FileName = target,
                WorkingDirectory = Path.GetDirectoryName(target),
                UseShellExecute = true
            });
            var timer = new Timer { Interval = 1050 };
            timer.Tick += delegate { timer.Stop(); timer.Dispose(); Close(); };
            timer.Start();
        }
        catch (Exception error)
        {
            MessageBox.Show(this, "Rapid 8D 没有成功打开。\r\n\r\n" + error.Message, "Rapid 8D", MessageBoxButtons.OK, MessageBoxIcon.Error);
            Close();
        }
    }
}

internal static class QuickLauncher
{
    [STAThread]
    private static int Main()
    {
        string folder = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
        string sibling = Path.Combine(folder, "Rapid8D.exe");
        string portable = Path.Combine(folder, "release", "Rapid8D", "Rapid8D.exe");
        string installed = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "Rapid8D", "Rapid8D.exe");
        string target = File.Exists(sibling) ? sibling : (File.Exists(portable) ? portable : installed);

        if (!File.Exists(target))
        {
            MessageBox.Show("没有找到 Rapid 8D 程序。\r\n\r\n请先运行 release 文件夹中的安装程序，或保留完整的 release\\Rapid8D 文件夹。", "Rapid 8D", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return 1;
        }

        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        Application.Run(new LaunchSplash(target));
        return 0;
    }
}
