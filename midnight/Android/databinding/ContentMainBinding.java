package com.example.neopasswd2.databinding;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import androidx.constraintlayout.widget.ConstraintLayout;
import androidx.viewbinding.ViewBinding;
import com.example.neopasswd2.R;

/* loaded from: classes7.dex */
public final class ContentMainBinding implements ViewBinding {
    private final ConstraintLayout rootView;

    private ContentMainBinding(ConstraintLayout rootView) {
        this.rootView = rootView;
    }

    @Override // androidx.viewbinding.ViewBinding
    public ConstraintLayout getRoot() {
        return this.rootView;
    }

    public static ContentMainBinding inflate(LayoutInflater inflater) {
        return inflate(inflater, null, false);
    }

    public static ContentMainBinding inflate(LayoutInflater inflater, ViewGroup parent, boolean attachToParent) {
        View root = inflater.inflate(R.layout.content_main, parent, false);
        if (attachToParent) {
            parent.addView(root);
        }
        return bind(root);
    }

    public static ContentMainBinding bind(View rootView) {
        if (rootView == null) {
            throw new NullPointerException("rootView");
        }
        return new ContentMainBinding((ConstraintLayout) rootView);
    }
}