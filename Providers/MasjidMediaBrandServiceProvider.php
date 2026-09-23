<?php

namespace Modules\MasjidMediaBrand\Providers;

use Illuminate\Support\ServiceProvider;
use Illuminate\Database\Eloquent\Factory;

class MasjidMediaBrandServiceProvider extends ServiceProvider
{
    /**
     * Indicates if loading of the provider is deferred.
     *
     * @var bool
     */
    protected $defer = false;

    /**
     * Boot the application events.
     *
     * @return void
     */
    public function boot()
    {
        $this->registerConfig();
        $this->registerViews();
        $this->registerFactories();
        $this->loadMigrationsFrom(__DIR__ . '/../Database/Migrations');
        $this->hooks();
    }

    /**
     * Module hooks.
     */
    public function hooks()
    {
        $publicPath = \Module::getPublicPath('masjidmediabrand');

        \Eventy::addFilter('layout.header_logo', function ($default) use ($publicPath) {
            return $publicPath.'/img/logo.png';
        });

        \Eventy::addFilter('layout.favicon', function ($default) use ($publicPath) {
            return $publicPath.'/img/favicon.ico';
        });

        \Eventy::addFilter('layout.theme_color', function ($default) {
            return '#0E1318';
        });

        \Eventy::addFilter('layout.title.name', function ($default) {
            return 'Masjid Media Helpdesk';
        });

        \Eventy::addFilter('login.banner', function ($default) use ($publicPath) {
            return $publicPath.'/img/logo.png';
        });

        \Eventy::addFilter('stylesheets', function ($stylesheets) use ($publicPath) {
            // Generated colour remap of core CSS (Tools/build_theme_base.py),
            // then the hand-tuned layer on top.
            $stylesheets[] = $publicPath.'/css/theme-base.css';
            $stylesheets[] = $publicPath.'/css/theme.css';

            return $stylesheets;
        });

        // Fonts need a real <link>: an @import inside the minified bundle is
        // invalid CSS mid-file and silently ignored.
        \Eventy::addAction('layout.head', function () {
            echo '<link rel="preconnect" href="https://fonts.bunny.net">'
                .'<link rel="stylesheet" href="https://fonts.bunny.net/css?family=fraunces:400,500,600,700|outfit:300,400,500,600&display=swap">';
        });

        \Eventy::addAction('body.class', function () {
            echo ' mm-theme';
        });

        \Eventy::addFilter('footer.text', function ($default) {
            $html = '&copy; '.date('Y').' Masjid Media &middot; '
                .'<a href="https://masjidmedia.id" target="_blank" rel="noopener">masjidmedia.id</a>';

            $source = config('masjidmediabrand.source_url');
            if ($source) {
                $html .= ' &middot; <a href="'.e($source).'" target="_blank" rel="noopener">Source</a>';
            }

            return $html;
        });

        // Only the "fancy" agent-reply template renders these hooks
        // (resources/views/emails/customer/reply_fancy.blade.php). The
        // separate auto-reply template does not, so the automatic
        // acknowledgement email stays unbranded for now.
        \Eventy::addFilter('reply_email.header', function ($default) use ($publicPath) {
            return '<div style="padding:16px 0;text-align:center;border-bottom:1px solid #eee;margin-bottom:16px;">'
                .'<img src="'.url($publicPath.'/img/logo.png').'" alt="Masjid Media" height="28">'
                .'</div>';
        });

        \Eventy::addFilter('reply_email.footer', function ($default) {
            return '<div style="padding:16px 0;text-align:center;border-top:1px solid #eee;margin-top:16px;color:#999;font-size:12px;">'
                .'Masjid Media &middot; <a href="https://masjidmedia.id">masjidmedia.id</a>'
                .'</div>';
        });
    }

    /**
     * Register the service provider.
     *
     * @return void
     */
    public function register()
    {
        $this->registerTranslations();
    }

    /**
     * Register config.
     *
     * @return void
     */
    protected function registerConfig()
    {
        $this->publishes([
            __DIR__.'/../Config/config.php' => config_path('masjidmediabrand.php'),
        ], 'config');
        $this->mergeConfigFrom(
            __DIR__.'/../Config/config.php', 'masjidmediabrand'
        );
    }

    /**
     * Register views.
     *
     * @return void
     */
    public function registerViews()
    {
        $viewPath = resource_path('views/modules/masjidmediabrand');

        $sourcePath = __DIR__.'/../Resources/views';

        $this->publishes([
            $sourcePath => $viewPath
        ],'views');

        $this->loadViewsFrom(array_merge(array_map(function ($path) {
            return $path . '/modules/masjidmediabrand';
        }, \Config::get('view.paths')), [$sourcePath]), 'masjidmediabrand');
    }

    /**
     * Register translations.
     *
     * @return void
     */
    public function registerTranslations()
    {
        $this->loadJsonTranslationsFrom(__DIR__ .'/../Resources/lang');
    }

    /**
     * Register an additional directory of factories.
     * @source https://github.com/sebastiaanluca/laravel-resource-flow/blob/develop/src/Modules/ModuleServiceProvider.php#L66
     */
    public function registerFactories()
    {
        if (! app()->environment('production')) {
            app(Factory::class)->load(__DIR__ . '/../Database/factories');
        }
    }

    /**
     * Get the services provided by the provider.
     *
     * @return array
     */
    public function provides()
    {
        return [];
    }
}
