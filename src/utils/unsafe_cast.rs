#[inline]
pub unsafe fn make_static<T>(ref_: &T) -> &'static T {
    std::mem::transmute::<&T, &'static T>(ref_)
}

#[inline]
pub unsafe fn make_static_mut<T>(ref_: &T) -> &'static mut T {
    &mut *(make_static(ref_) as *const T as *mut T)
}

#[inline]
pub unsafe fn make_mut<T>(ref_: &T) -> &'static mut T {
    &mut *(ref_ as *const T as *mut T)
}
