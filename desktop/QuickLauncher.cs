using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Net;
using System.Reflection;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Windows.Forms;

[assembly: AssemblyTitle("启动 Rapid 8D")]
[assembly: AssemblyProduct("Rapid 8D")]
[assembly: AssemblyVersion("0.5.0.0")]
[assembly: AssemblyFileVersion("0.5.0.0")]

internal sealed class Rapid8DContext : ApplicationContext
{
    private readonly string fileName;
    private readonly string arguments;
    private readonly string workingDirectory;
    private readonly Form splash;
    private readonly NotifyIcon tray;
    private bool exiting;

    internal Rapid8DContext(string fileName, string arguments, string workingDirectory)
    {
        this.fileName = fileName;
        this.arguments = arguments ?? "";
        this.workingDirectory = workingDirectory;
        splash = BuildSplash();
        tray = BuildTray();
        splash.Shown += delegate { splash.BeginInvoke(new Action(StartApplication)); };
        splash.Show();
    }

    private Form BuildSplash()
    {
        var form = new Form {
            ClientSize = new Size(560, 318),
            StartPosition = FormStartPosition.CenterScreen,
            FormBorderStyle = FormBorderStyle.None,
            BackColor = Color.FromArgb(18, 51, 74),
            ShowInTaskbar = true,
            TopMost = true
        };
        var edge = new Panel { Dock = DockStyle.Fill, Padding = new Padding(1), BackColor = Color.FromArgb(48, 136, 140) };
        var surface = new Panel { Dock = DockStyle.Fill, BackColor = Color.FromArgb(18, 51, 74) };
        edge.Controls.Add(surface);
        var mark = new Label {
            Text = "8D", TextAlign = ContentAlignment.MiddleCenter, Location = new Point(43, 43), Size = new Size(54, 54),
            Font = new Font("Georgia", 17, FontStyle.Bold), ForeColor = Color.White, BackColor = Color.FromArgb(17, 125, 131)
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
        var progress = new ProgressBar {
            Location = new Point(44, 200), Size = new Size(472, 5),
            Style = ProgressBarStyle.Marquee, MarqueeAnimationSpeed = 26
        };
        var method = new Label {
            Text = "FACTS  ·  EVIDENCE  ·  VERIFICATION  ·  PREVENTION", AutoSize = true, Location = new Point(44, 221),
            Font = new Font("Segoe UI", 7), ForeColor = Color.FromArgb(92, 169, 172)
        };
        var credit = new Label {
            Text = "BUILT & CURATED BY 刘鸿志   ·   v0.5.0", AutoSize = true, Location = new Point(44, 273),
            Font = new Font("Microsoft YaHei UI", 8), ForeColor = Color.FromArgb(120, 155, 166)
        };
        surface.Controls.AddRange(new Control[] { mark, name, subtitle, rule, message, progress, method, credit });
        form.Controls.Add(edge);
        return form;
    }

    private NotifyIcon BuildTray()
    {
        var menu = new ContextMenuStrip();
        var open = new ToolStripMenuItem("打开 Rapid 8D") { Font = new Font(SystemFonts.MenuFont, FontStyle.Bold) };
        open.Click += delegate { OpenWorkbench(); };
        var exit = new ToolStripMenuItem("退出 Rapid 8D");
        exit.Click += delegate { ExitDesktop(); };
        menu.Items.Add(open);
        menu.Items.Add(new ToolStripSeparator());
        menu.Items.Add(exit);
        var icon = new NotifyIcon {
            Icon = TryApplicationIcon() ?? SystemIcons.Application,
            Text = "Rapid 8D · 质量问题研析工作台",
            ContextMenuStrip = menu,
            Visible = false
        };
        icon.DoubleClick += delegate { OpenWorkbench(); };
        return icon;
    }

    private void StartApplication()
    {
        try
        {
            LaunchTarget();
            tray.Visible = true;
            var timer = new System.Windows.Forms.Timer { Interval = 1050 };
            timer.Tick += delegate {
                timer.Stop();
                timer.Dispose();
                splash.Hide();
                splash.ShowInTaskbar = false;
                tray.ShowBalloonTip(1800, "Rapid 8D 已启动", "关闭窗口后，可从右下角通知区域再次打开。", ToolTipIcon.Info);
            };
            timer.Start();
        }
        catch (Exception error)
        {
            splash.Hide();
            MessageBox.Show("Rapid 8D 没有成功打开。\r\n\r\n" + error.Message, "Rapid 8D", MessageBoxButtons.OK, MessageBoxIcon.Error);
            ExitDesktop();
        }
    }

    private void OpenWorkbench()
    {
        if (exiting) return;
        try { LaunchTarget(); }
        catch (Exception error) { MessageBox.Show(error.Message, "Rapid 8D", MessageBoxButtons.OK, MessageBoxIcon.Error); }
    }

    private void LaunchTarget()
    {
        Process.Start(new ProcessStartInfo {
            FileName = fileName,
            Arguments = arguments,
            WorkingDirectory = workingDirectory,
            UseShellExecute = false,
            CreateNoWindow = true
        });
    }

    private void ExitDesktop()
    {
        if (exiting) return;
        exiting = true;
        tray.Visible = false;
        RequestServerQuit();
        tray.Dispose();
        splash.Dispose();
        ExitThread();
    }

    private static void RequestServerQuit()
    {
        try
        {
            string session = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Rapid8D", "session.json");
            if (!File.Exists(session)) return;
            string json = File.ReadAllText(session, Encoding.UTF8);
            Match portMatch = Regex.Match(json, @"""port""\s*:\s*(\d+)");
            Match tokenMatch = Regex.Match(json, @"""token""\s*:\s*""([^""]+)""");
            if (!portMatch.Success || !tokenMatch.Success) return;
            var request = (HttpWebRequest)WebRequest.Create("http://127.0.0.1:" + portMatch.Groups[1].Value + "/api/quit");
            request.Method = "POST";
            request.ContentType = "application/json";
            request.Headers["X-Rapid-Token"] = tokenMatch.Groups[1].Value;
            request.Timeout = 1800;
            byte[] body = Encoding.UTF8.GetBytes("{}");
            request.ContentLength = body.Length;
            using (Stream stream = request.GetRequestStream()) stream.Write(body, 0, body.Length);
            using (var response = (HttpWebResponse)request.GetResponse()) { }
        }
        catch { }
    }

    protected override void ExitThreadCore()
    {
        tray.Visible = false;
        tray.Dispose();
        base.ExitThreadCore();
    }

    private static Icon TryApplicationIcon()
    {
        try { return Icon.ExtractAssociatedIcon(Application.ExecutablePath); }
        catch { return null; }
    }
}

internal static class QuickLauncher
{
    private static Mutex instanceMutex;

    private static bool TryPlan(out string fileName, out string arguments, out string workingDirectory, out string error)
    {
        fileName = arguments = workingDirectory = error = null;
        string folder = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
        string entry = Path.Combine(folder, "desktop_entry.py");
        if (File.Exists(entry))
        {
            string python = FindPython();
            if (python == null)
            {
                error = "没有找到 Python。\r\n\r\n请安装 Python 3.11 或 3.12 后再双击「启动 Rapid 8D」。";
                return false;
            }
            fileName = python;
            arguments = "\"" + entry + "\"";
            workingDirectory = folder;
            return true;
        }
        string sibling = Path.Combine(folder, "Rapid8D.exe");
        string portable = Path.Combine(folder, "release", "Rapid8D", "Rapid8D.exe");
        string installed = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "Rapid8D", "Rapid8D.exe");
        string target = File.Exists(sibling) ? sibling : (File.Exists(portable) ? portable : installed);
        if (!File.Exists(target))
        {
            error = "没有找到 Rapid 8D 程序。";
            return false;
        }
        fileName = target;
        arguments = "";
        workingDirectory = Path.GetDirectoryName(target);
        return true;
    }

    private static string FindPython()
    {
        string local = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        string programs = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles);
        string[] roots = {
            Path.Combine(local, "Programs", "Python", "Python312"),
            Path.Combine(local, "Programs", "Python", "Python311"),
            Path.Combine(programs, "Python312"),
            Path.Combine(programs, "Python311")
        };
        foreach (string root in roots)
        {
            string pythonw = Path.Combine(root, "pythonw.exe");
            if (File.Exists(pythonw)) return pythonw;
        }
        string path = Environment.GetEnvironmentVariable("PATH") ?? "";
        foreach (string dir in path.Split(';'))
        {
            string trimmed = dir.Trim();
            if (trimmed.Length == 0 || trimmed.IndexOf("codex-runtimes", StringComparison.OrdinalIgnoreCase) >= 0) continue;
            string pythonw = Path.Combine(trimmed, "pythonw.exe");
            if (File.Exists(pythonw)) return pythonw;
        }
        string codex = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".cache", "codex-runtimes", "codex-primary-runtime", "dependencies", "python", "pythonw.exe");
        if (File.Exists(codex)) return codex;
        return null;
    }

    [STAThread]
    private static int Main()
    {
        string fileName, arguments, workingDirectory, error;
        if (!TryPlan(out fileName, out arguments, out workingDirectory, out error))
        {
            MessageBox.Show(error, "Rapid 8D", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return 1;
        }

        bool first;
        instanceMutex = new Mutex(true, "Local\\Rapid8D-Tray-v1", out first);
        if (!first)
        {
            try
            {
                Process.Start(new ProcessStartInfo { FileName = fileName, Arguments = arguments, WorkingDirectory = workingDirectory, UseShellExecute = false, CreateNoWindow = true });
                return 0;
            }
            catch { return 2; }
        }

        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        Application.Run(new Rapid8DContext(fileName, arguments, workingDirectory));
        instanceMutex.ReleaseMutex();
        instanceMutex.Dispose();
        return 0;
    }
}
