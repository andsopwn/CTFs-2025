package com.example.neopasswd2.databinding;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import androidx.viewbinding.ViewBinding;
import androidx.viewbinding.ViewBindings;
import com.example.neopasswd2.R;

/* loaded from: classes7.dex */
public final class NavHeaderMainBinding implements ViewBinding {
    public final ImageView imageView;
    private final LinearLayout rootView;
    public final TextView textView;

    private NavHeaderMainBinding(LinearLayout rootView, ImageView imageView, TextView textView) {
        this.rootView = rootView;
        this.imageView = imageView;
        this.textView = textView;
    }

    @Override // androidx.viewbinding.ViewBinding
    public LinearLayout getRoot() {
        return this.rootView;
    }

    public static NavHeaderMainBinding inflate(LayoutInflater inflater) {
        return inflate(inflater, null, false);
    }

    public static NavHeaderMainBinding inflate(LayoutInflater inflater, ViewGroup parent, boolean attachToParent) {
        View root = inflater.inflate(R.layout.nav_header_main, parent, false);
        if (attachToParent) {
            parent.addView(root);
        }
        return bind(root);
    }

    public static NavHeaderMainBinding bind(View rootView) {
        int id = R.id.imageView;
        ImageView imageView = (ImageView) ViewBindings.findChildViewById(rootView, id);
        if (imageView != null) {
            id = R.id.textView;
            TextView textView = (TextView) ViewBindings.findChildViewById(rootView, id);
            if (textView != null) {
                return new NavHeaderMainBinding((LinearLayout) rootView, imageView, textView);
            }
        }
        String missingId = rootView.getResources().getResourceName(id);
        throw new NullPointerException("Missing required view with ID: ".concat(missingId));
    }
}