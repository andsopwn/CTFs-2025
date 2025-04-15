package com.example.neopasswd2.databinding;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import androidx.drawerlayout.widget.DrawerLayout;
import androidx.viewbinding.ViewBinding;
import androidx.viewbinding.ViewBindings;
import com.example.neopasswd2.R;
import com.google.android.material.navigation.NavigationView;

/* loaded from: classes7.dex */
public final class ActivityMainBinding implements ViewBinding {
    public final AppBarMainBinding appBarMain;
    public final DrawerLayout drawerLayout;
    public final NavigationView navView;
    private final DrawerLayout rootView;

    private ActivityMainBinding(DrawerLayout rootView, AppBarMainBinding appBarMain, DrawerLayout drawerLayout, NavigationView navView) {
        this.rootView = rootView;
        this.appBarMain = appBarMain;
        this.drawerLayout = drawerLayout;
        this.navView = navView;
    }

    @Override // androidx.viewbinding.ViewBinding
    public DrawerLayout getRoot() {
        return this.rootView;
    }

    public static ActivityMainBinding inflate(LayoutInflater inflater) {
        return inflate(inflater, null, false);
    }

    public static ActivityMainBinding inflate(LayoutInflater inflater, ViewGroup parent, boolean attachToParent) {
        View root = inflater.inflate(R.layout.activity_main, parent, false);
        if (attachToParent) {
            parent.addView(root);
        }
        return bind(root);
    }

    public static ActivityMainBinding bind(View rootView) {
        int id = R.id.app_bar_main;
        View appBarMain = ViewBindings.findChildViewById(rootView, id);
        if (appBarMain != null) {
            AppBarMainBinding binding_appBarMain = AppBarMainBinding.bind(appBarMain);
            DrawerLayout drawerLayout = (DrawerLayout) rootView;
            id = R.id.nav_view;
            NavigationView navView = (NavigationView) ViewBindings.findChildViewById(rootView, id);
            if (navView != null) {
                return new ActivityMainBinding((DrawerLayout) rootView, binding_appBarMain, drawerLayout, navView);
            }
        }
        String missingId = rootView.getResources().getResourceName(id);
        throw new NullPointerException("Missing required view with ID: ".concat(missingId));
    }
}