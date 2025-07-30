module.exports = {
  webpack: {
    configure: (webpackConfig) => {
      // Disable webpack cache for development
      if (process.env.NODE_ENV === 'development') {
        webpackConfig.cache = false;
      }
      
      // Configure webpack-dev-server for better hot reload
      if (webpackConfig.devServer) {
        webpackConfig.devServer = {
          ...webpackConfig.devServer,
          hot: true,
          liveReload: true,
          watchFiles: ['src/**/*'],
          static: {
            watch: true,
          },
        };
      }
      
      // Ensure file system cache is properly invalidated
      webpackConfig.snapshot = {
        managedPaths: [],
        immutablePaths: [],
      };
      
      return webpackConfig;
    },
  },
};