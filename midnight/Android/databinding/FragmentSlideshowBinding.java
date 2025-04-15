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
public final class FragmentSlideshowBinding implements ViewBinding {
    private final ConstraintLayout rootView;
    public final TextView textSlideshow;

    private FragmentSlideshowBinding(ConstraintLayout rootView, TextView textSlideshow) {
        this.rootView = rootView;
        this.textSlideshow = textSlideshow;
    }

    @Override // androidx.viewbinding.ViewBinding
    public ConstraintLayout getRoot() {
        return this.rootView;
    }

    public static FragmentSlideshowBinding inflate(LayoutInflater inflater) {
        return inflate(inflater, null, false);
    }

    public static FragmentSlideshowBinding inflate(LayoutInflater inflater, ViewGroup parent, boolean attachToParent) {
        View root = inflater.inflate(R.layout.fragment_slideshow, parent, false);
        if (attachToParent) {
            parent.addView(root);
        }
        return bind(root);
    }

    public static FragmentSlideshowBinding bind(View rootView) {
        int id = R.id.text_slideshow;
        TextView textSlideshow = (TextView) ViewBindings.findChildViewById(rootView, id);
        if (textSlideshow != null) {
            return new FragmentSlideshowBinding((ConstraintLayout) rootView, textSlideshow);
        }
        String missingId = rootView.getResources().getResourceName(id);
        throw new NullPointerException("Missing required view with ID: ".concat(missingId));
    }
}