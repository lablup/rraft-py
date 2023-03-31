#![allow(clippy::cast_ref_to_mut)]

/// # Safety
///
/// TODO: Write some warnings here.
#[inline]
pub unsafe fn make_static<T>(ref_: &T) -> &'static T {
    std::mem::transmute::<&T, &'static T>(ref_)
}

/// # Safety
///
/// TODO: Write some warnings here.
#[inline]
pub unsafe fn make_static_mut<T>(ref_: &T) -> &'static mut T {
    &mut *(make_static(ref_) as *const T as *mut T)
}

/// # Safety
///
/// TODO: Write some warnings here.
#[inline]
pub unsafe fn make_mut<T>(ref_: &T) -> &'static mut T {
    &mut *(ref_ as *const T as *mut T)
}
