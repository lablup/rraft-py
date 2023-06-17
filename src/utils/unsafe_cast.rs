#![allow(clippy::cast_ref_to_mut)]

/// # Safety
///
/// TODO: Write some warnings here.
#[inline]
pub unsafe fn make_static<T: ?Sized>(ref_: &T) -> &'static T {
    std::mem::transmute::<&T, &'static T>(ref_)
}

/// # Safety
///
/// TODO: Write some warnings here.
#[inline]
pub unsafe fn make_static_mut<T: ?Sized>(ref_: &T) -> &'static mut T {
    #![allow(cast_ref_to_mut)]
    unsafe { &mut *(make_static(ref_) as *const T as *mut T) }
}

/// # Safety
///
/// TODO: Write some warnings here.
#[inline]
pub unsafe fn make_mut<T: ?Sized>(ref_: &T) -> &mut T {
    #![allow(clippy::mut_from_ref)]
    #![allow(cast_ref_to_mut)]
    &mut *(ref_ as *const T as *mut T)
}
