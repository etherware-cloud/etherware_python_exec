from .exec.mainloop import MainLoop, MyDaemon

if __name__ == '__main__':
    daemon = MainLoop()
    daemon.start()
