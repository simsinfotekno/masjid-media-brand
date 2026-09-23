<?php

Route::group(['middleware' => 'web', 'prefix' => \Helper::getSubdirectory(), 'namespace' => 'Modules\MasjidMediaBrand\Http\Controllers'], function()
{
    Route::get('/', 'MasjidMediaBrandController@index');
});
