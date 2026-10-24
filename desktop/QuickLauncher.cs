using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Windows.Forms;

[assembly: AssemblyTitle("启动 Rapid 8D")]
[assembly: AssemblyProduct("Rapid 8D")]
[assembly: AssemblyVersion("0.2.0.0")]
[assembly: AssemblyFileVersion("0.2.0.0")]

internal static class QuickLauncher
{
    [STAThread]
    private static int Main()
    {
        string folder = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
        string portable = Path.Combine(folder, "release", "Rapid8D", "Rapid8D.exe");
        string installed = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "Programs", "Rapid8D", "Rapid8D.exe");

        string target = File.Exists(portable) ? portable : installed;
        if (!File.Exists(target))
        {
            MessageBox.Show(
                "没有找到 Rapid 8D 程序。\r\n\r\n请先双击 release 文件夹中的 Rapid8D-Setup.exe 完成安装，或保留完整的 release\\Rapid8D 文件夹。",
                "Rapid 8D",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information);
            return 1;
        }

        try
        {
            Process.Start(new ProcessStartInfo
            {
                FileName = target,
                WorkingDirectory = Path.GetDirectoryName(target),
                UseShellExecute = true
            });
            return 0;
        }
        catch (Exception error)
        {
            MessageBox.Show(
                "Rapid 8D 没有成功打开。\r\n\r\n" + error.Message,
                "Rapid 8D",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error);
            return 2;
        }
    }
}
