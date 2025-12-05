{pkgs}: {
  channel = "stable-24.05";
  packages = [
    pkgs.nodejs_20, # npm is included with nodejs
    (pkgs.python3.withPackages (ps: [
      # Dependencies from requirements.txt are declared here
      ps.requests
      ps.beautifulsoup4
      ps.google-generativeai
      # ps.pip # pip is still available if needed for other tasks
    ])),
    pkgs.google-cloud-sdk
  ];
  idx.extensions = [
    "svelte.svelte-vscode",
    "vue.volar"
  ];
  idx.previews = {
    web = {
      command = [
        "npm",
        "run",
        "dev"
      ];
      env = {
        PORT = "$PORT";
      };
      manager = "web";
    };
  };
  # The startTasks section is no longer needed for Python dependencies
  # as they are now managed declaratively by Nix.
  idx.startTasks = [];
}