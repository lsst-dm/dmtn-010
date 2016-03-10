# Person-to-person discussions

## Erik T.

gWCS is being written with outside use foremost in mind.

## Perry and Nadia

Perry: the problem wasn't AST's functionality, but people having looked and the code and not wanted to bring it into the python stack.

On requirements: flexibility and distortion models
Nadia:
 * we needed to do fitting within the framework. AST can combine models in different ways, but cannot do fitting.
 * easy extension of models by users. Needed to allow users to add their own models without knowing the guts (harder in AST).
Perry:
 * Easier connection between fitting of WCS models.
 * Ability to include in the WCS models other parameters that might affect the transforms. e.g. effects that depend on time, spectral orders.
 * Tweak the model after the fact, using those other parameters.

Nadia on HST:
 * imaging instruments have SIP+distortions, also timing corrections for ACS.
Perry:
 * Those doing mosaicing now achieve 2/100 of pixel distortion models.
 * Current system is FITS+stuff, which is a mess to maintain.
 * Don't know if there are stringent requirements written down for JWST.

 * HST and JWST are required to share their data in FITS.
 * For imaging and things where it makes sense, they will include an approximation in the FITS WCS model, with the ASDF output as a separate extension.
 * May produce an optional exact pixel map.

Nadia on gWCS status
 * Mostly complete for JWST instruments.
 * Excluding the imaging instruments, every one has their own way of doing distortions.
 * Imaging instruments use polynomials plus other corrections for e.g. filter.
 * NEARSPEC the WCS is a chained optical model through the instrument.
  * The model is fixed, but for each observation the position of the grating wheel is not repeatable so there's an extra correction for that. The transform through the filters is chromatic, so you have to include spectral terms.
 * If there was a time/temperature dependent effect, we would include the parameter for that in the output, with a pre-computed model.

 * Don't have benchmarks, so can't obviously compare speed with AST.
 
 * Have talked about collapsing models, but haven't had time yet.

## David Berry (AST)

 * No knowledge off gWCS.
 * "I always find it surprising that people find AST as hard to use as they do."
  * "I don't know if that's because treating WCS in object oriented fashion is hard, or something else."
 * Reimplenenting AST in C++/modern fashion would be good for longterm maintainability.
 * There is a test suite, but would not claim it to be complete.
  * test suite has ad hoc coverage.
 
 * AST doesn't do fitting: you fit the mappings in some other software, and push them into AST.
  * This is process done in SCUBA2/JCMT code.
  * SCUBA2 distortions are not refined after the fact: they were pre-computed and are used as-is.

Performance
 * SCUBA2 had requirement to create good maps in real time.
 * AST speed was a problem initially.
 * Composite mappings were a problem: it's very easy to join mappings together to create complicated mappings that take forever to apply.
 * Even with the simplification, speed could still be a problem.
 * Linear approximation
  * It depends on how linear the transformation is and how much accuracy you want.
 * Personally has not used AST on 4k equivalent exposure. Never had a report from anyone that it's too slow.
 * AST is a big system: there's probably a lot of it that wouldn't be of interest to LSST.

Time/temperature varying distortions
 * AST does not have a time/temperature mapping, e.g. polymap would have to be modified.
 * Something where the parameters of the mapping would have to be changed from another input.

Adding mappings
 * Simple mappings are quite easy, using an existing mapping as a template.
 * More complicated ones (e.g. time varying above) are more difficult.
 * There's a lot of the code that one wouldn't have to ever look at.
 * Nobody else has been interested until recently in writing new mappings, but could write a document to assist this.
 * Mappings are the easiest class to create. Frames are more difficult, because of the ability for AST to work out the mapping between two arbitrary frames (if it exists).
 * Spectral coordinate systems are quite difficult.

Composition/pixel->sky->pixel (stacking/differencing two images)
 * If the tangent points are different, you have to go to the sky.
 * We could define things so the tangent points are the same.
 * So long as we define everything in ICRS, this is trivial.
  * If not ICRS (e.g. one in FK5 one in galactic), AST has intelligence for collapsing the mapping.

Consulting?
 * Direct employment (move him from Hawaii to LSST).
 * Contracting work in evenings and weekends.
 * LSST buying some of his time from Hawaii.
 * In principle, it would be a very interesting thing to do.
 * It would be a very hard decision to make: there's a new polarimeter going onto SCUBA2 soon. I would be sad (and the project a bit lost) if I left the project before it produced science. Timeline roughly 6-12 months from now.
 * In terms of actually leaving the job, it would take a lot of thinking.
 
 * How long would it take to reimplement the minimal requirements for AST in C++?
  * To replace the macro layer in C++ feels like about 6 months of work.
  * A lot of the work would be coming up with the design. Actually implementing it would be less work.
  * It would be good to have someone else with their head around the system.
  * "If I was 30 rather than 55, I would say I'll be around and able to maintain the system. Retirement is dangling in front of me, so it would make life easier for others to contribute if we reimplemented it."
  * The API would have to change (function pointers are passed into the AST functions).
  * "To be honest: I've never written a line of C++ in my life."
  * "I've heard people say that the python interface is not very pythonic. I'm not a python expert."
  * "The C examples will look smoother than the python examples."

Data input/output
 * AST has a heirarchical text format.
 * The channel system is designed to transform between different formats.
 * The big question is if there is a mismatch between e.g. astropy.model(s) and AST Mappings.
 * Wrote a channel class for IVOA's SpaceTimeCoordinates.
 * Given a description of the format (and assuming the representations are similar), an ASDF channel should be able to be written.

Anything else?
 * IVOA has some kind of system, but don't know any details. They claim to have chainable mappings. Mark Christelo-something?
 * Have been able to define new types of mappings: AST has proven to be extensible.
