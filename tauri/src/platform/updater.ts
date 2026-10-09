import type { PlatformUpdater, UpdateStatus } from '@/platform/types';

// Community previews use manual releases. Never install upstream binaries over
// the patched runtime, and do not report this preview as officially up to date.
class CommunityUpdater implements PlatformUpdater {
  private status: UpdateStatus = {
    checking: false,
    available: false,
    downloading: false,
    installing: false,
    readyToInstall: false,
  };

  subscribe(callback: (status: UpdateStatus) => void): () => void {
    callback(this.getStatus());
    return () => {};
  }

  getStatus(): UpdateStatus {
    return { ...this.status };
  }

  async checkForUpdates(): Promise<void> {}
  async downloadAndInstall(): Promise<void> {}
  async restartAndInstall(): Promise<void> {}
}

export const tauriUpdater = new CommunityUpdater();
