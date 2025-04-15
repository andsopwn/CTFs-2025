package com.example.neopasswd2.databinding;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.constraintlayout.widget.ConstraintLayout;
import androidx.viewbinding.ViewBinding;
import androidx.viewbinding.ViewBindings;
import com.example.neopasswd2.R;

/* loaded from: classes7.dex */
public final class FragmentHomeBinding implements ViewBinding {
    private final ConstraintLayout rootView;
    public final TextView textHome;

    private FragmentHomeBinding(ConstraintLayout rootView, TextView textHome) {
        this.rootView = rootView;
        this.textHome = textHome;
    }

    @Override // androidx.viewbinding.ViewBinding
    public ConstraintLayout getRoot() {
        return this.rootView;
    }

    public static FragmentHomeBinding inflate(LayoutInflater inflater) {
        return inflate(inflater, null, false);
    }

    public static FragmentHomeBinding inflate(LayoutInflater inflater, ViewGroup parent, boolean attachToParent) {
        View root = inflater.inflate(R.layout.fragment_home, parent, false);
        if (attachToParent) {
            parent.addView(root);
        }
        return bind(root);
    }

    public static FragmentHomeBinding bind(View rootView) {
        int id = R.id.text_home;
        TextView textHome = (TextView) ViewBindings.findChildViewById(rootView, id);
        if (textHome != null) {
            return new FragmentHomeBinding((ConstraintLayout) rootView, textHome);
        }
        String missingId = rootView.getResources().getResourceName(id);
        throw new NullPointerException("Missing required view with ID: ".concat(missingId));
    }
}