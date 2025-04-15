package com.example.neopasswd2.databinding;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.LinearLayout;
import androidx.viewbinding.ViewBinding;
import androidx.viewbinding.ViewBindings;
import com.example.neopasswd2.R;

/* loaded from: classes7.dex */
public final class ActivityLoginBinding implements ViewBinding {
    public final EditText editPassword;
    public final EditText editUsername;
    private final LinearLayout rootView;

    private ActivityLoginBinding(LinearLayout rootView, EditText editPassword, EditText editUsername) {
        this.rootView = rootView;
        this.editPassword = editPassword;
        this.editUsername = editUsername;
    }

    @Override // androidx.viewbinding.ViewBinding
    public LinearLayout getRoot() {
        return this.rootView;
    }

    public static ActivityLoginBinding inflate(LayoutInflater inflater) {
        return inflate(inflater, null, false);
    }

    public static ActivityLoginBinding inflate(LayoutInflater inflater, ViewGroup parent, boolean attachToParent) {
        View root = inflater.inflate(R.layout.activity_login, parent, false);
        if (attachToParent) {
            parent.addView(root);
        }
        return bind(root);
    }

    public static ActivityLoginBinding bind(View rootView) {
        int id = R.id.editPassword;
        EditText editPassword = (EditText) ViewBindings.findChildViewById(rootView, id);
        if (editPassword != null) {
            id = R.id.editUsername;
            EditText editUsername = (EditText) ViewBindings.findChildViewById(rootView, id);
            if (editUsername != null) {
                return new ActivityLoginBinding((LinearLayout) rootView, editPassword, editUsername);
            }
        }
        String missingId = rootView.getResources().getResourceName(id);
        throw new NullPointerException("Missing required view with ID: ".concat(missingId));
    }
}