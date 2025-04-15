package com.example.neopasswd2.databinding;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.appcompat.widget.Toolbar;
import androidx.coordinatorlayout.widget.CoordinatorLayout;
import androidx.viewbinding.ViewBinding;
import androidx.viewbinding.ViewBindings;
import com.example.neopasswd2.R;
import com.google.android.material.floatingactionbutton.FloatingActionButton;

/* loaded from: classes7.dex */
public final class AppBarMainBinding implements ViewBinding {
    public final FloatingActionButton fab;
    private final CoordinatorLayout rootView;
    public final Toolbar toolbar;
    public final TextView welcomeText;

    private AppBarMainBinding(CoordinatorLayout rootView, FloatingActionButton fab, Toolbar toolbar, TextView welcomeText) {
        this.rootView = rootView;
        this.fab = fab;
        this.toolbar = toolbar;
        this.welcomeText = welcomeText;
    }

    @Override // androidx.viewbinding.ViewBinding
    public CoordinatorLayout getRoot() {
        return this.rootView;
    }

    public static AppBarMainBinding inflate(LayoutInflater inflater) {
        return inflate(inflater, null, false);
    }

    public static AppBarMainBinding inflate(LayoutInflater inflater, ViewGroup parent, boolean attachToParent) {
        View root = inflater.inflate(R.layout.app_bar_main, parent, false);
        if (attachToParent) {
            parent.addView(root);
        }
        return bind(root);
    }

    public static AppBarMainBinding bind(View rootView) {
        int id = R.id.fab;
        FloatingActionButton fab = (FloatingActionButton) ViewBindings.findChildViewById(rootView, id);
        if (fab != null) {
            id = R.id.toolbar;
            Toolbar toolbar = (Toolbar) ViewBindings.findChildViewById(rootView, id);
            if (toolbar != null) {
                id = R.id.welcomeText;
                TextView welcomeText = (TextView) ViewBindings.findChildViewById(rootView, id);
                if (welcomeText != null) {
                    return new AppBarMainBinding((CoordinatorLayout) rootView, fab, toolbar, welcomeText);
                }
            }
        }
        String missingId = rootView.getResources().getResourceName(id);
        throw new NullPointerException("Missing required view with ID: ".concat(missingId));
    }
}