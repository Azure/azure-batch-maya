﻿//------------------------------------------------------------------------------
// <auto-generated>
//     This code was generated by a tool.
//     Runtime Version:4.0.30319.34014
//
//     Changes to this file may cause incorrect behavior and will be lost if
//     the code is regenerated.
// </auto-generated>
//------------------------------------------------------------------------------

namespace Maya.Cloud {
    using System;
    
    
    /// <summary>
    ///   A strongly-typed resource class, for looking up localized strings, etc.
    /// </summary>
    // This class was auto-generated by the StronglyTypedResourceBuilder
    // class via a tool like ResGen or Visual Studio.
    // To add or remove a member, edit your .ResX file then rerun ResGen
    // with the /str option, or rebuild your VS project.
    [global::System.CodeDom.Compiler.GeneratedCodeAttribute("System.Resources.Tools.StronglyTypedResourceBuilder", "4.0.0.0")]
    [global::System.Diagnostics.DebuggerNonUserCodeAttribute()]
    [global::System.Runtime.CompilerServices.CompilerGeneratedAttribute()]
    internal class MayaScripts {
        
        private static global::System.Resources.ResourceManager resourceMan;
        
        private static global::System.Globalization.CultureInfo resourceCulture;
        
        [global::System.Diagnostics.CodeAnalysis.SuppressMessageAttribute("Microsoft.Performance", "CA1811:AvoidUncalledPrivateCode")]
        internal MayaScripts() {
        }
        
        /// <summary>
        ///   Returns the cached ResourceManager instance used by this class.
        /// </summary>
        [global::System.ComponentModel.EditorBrowsableAttribute(global::System.ComponentModel.EditorBrowsableState.Advanced)]
        internal static global::System.Resources.ResourceManager ResourceManager {
            get {
                if (object.ReferenceEquals(resourceMan, null)) {
                    global::System.Resources.ResourceManager temp = new global::System.Resources.ResourceManager("Maya.Cloud.MayaScripts", typeof(MayaScripts).Assembly);
                    resourceMan = temp;
                }
                return resourceMan;
            }
        }
        
        /// <summary>
        ///   Overrides the current thread's CurrentUICulture property for all
        ///   resource lookups using this strongly typed resource class.
        /// </summary>
        [global::System.ComponentModel.EditorBrowsableAttribute(global::System.ComponentModel.EditorBrowsableState.Advanced)]
        internal static global::System.Globalization.CultureInfo Culture {
            get {
                return resourceCulture;
            }
            set {
                resourceCulture = value;
            }
        }
        
        /// <summary>
        ///   Looks up a localized string similar to &lt;?xml version=&quot;1.0&quot; encoding=&quot;utf-8&quot;?&gt;
        ///&lt;ADLMCUSTOMENV VERSION=&quot;1.0.0.0&quot;&gt;
        ///    &lt;PLATFORM OS=&quot;Windows&quot;&gt;
        ///        &lt;KEY ID=&quot;ADLM_COMMON_BIN_LOCATION&quot;&gt;
        ///            &lt;!--Path to the AdLM shared executables--&gt;
        ///            &lt;STRING&gt;{0}\Common Files\Autodesk Shared\Adlm\R&lt;/STRING&gt;
        ///        &lt;/KEY&gt;
        ///        &lt;KEY ID=&quot;ADLM_COMMON_LIB_LOCATION&quot;&gt;
        ///            &lt;!--Path to the AdLM shared libraries--&gt;
        ///            &lt;STRING&gt;{0}\Common Files\Autodesk Shared\Adlm\R&lt;/STRING&gt;
        ///        &lt;/KEY&gt;
        ///        &lt;KEY ID=&quot;ADLM_COMMON_LOCALIZ [rest of string was truncated]&quot;;.
        /// </summary>
        internal static string client {
            get {
                return ResourceManager.GetString("client", resourceCulture);
            }
        }
        
        /// <summary>
        ///   Looks up a localized string similar to global proc renderPrep() 
        ///{{ 
        ///{0} 
        ///{1}
        ///}}.
        /// </summary>
        internal static string dirMap {
            get {
                return ResourceManager.GetString("dirMap", resourceCulture);
            }
        }
        
        /// <summary>
        ///   Looks up a localized string similar to MAYA_MODULE_PATH ={0}/{3}/modules;{1}/{4}/modules;{1};{0}/Common Files/Autodesk Shared/Modules/maya/{5}
        ///FBX_LOCATION = {0}/{3}/plug-ing/fbx/
        ///MENTALRAY_LOCATION = {0}/mentalrayForMaya{5}/
        ///MAYA_SCRIPT_BASE = {0}/{3}
        ///TEMP = {2}
        ///MAYA_LOCATION = {0}\{3}
        ///TMPDIR = {2}
        ///MENTALRAY_BIN_LOCATION = {0}/mentalrayForMaya{5}/bin
        ///MAYA_PLUG_IN_PATH = {1};{0}/{3}/bin/plug-ins;{0}/{3}/plug-ins/bifrost/plug-ins;{0}/{3}/plug-ins/fbx/plug-ins;{0}/mentalrayForMaya{5}/plug-ins;{0}/solidangle/mtoadeploy/{5}/plug-ins;{0}/{3}/ [rest of string was truncated]&quot;;.
        /// </summary>
        internal static string env {
            get {
                return ResourceManager.GetString("env", resourceCulture);
            }
        }
        
        /// <summary>
        ///   Looks up a localized string similar to AUTODESK_ADLM_THINCLIENT_ENV={0}\Adlm\AdlmThinClientCustomEnv.xml
        ///MAYA_LICENSE=unlimited
        ///MAYA_LICENSE_METHOD=network.
        /// </summary>
        internal static string lic {
            get {
                return ResourceManager.GetString("lic", resourceCulture);
            }
        }
        
        /// <summary>
        ///   Looks up a localized string similar to //Maya 2015 Project Definition
        ///
        ///
        ///
        ///workspace -fr &quot;fluidCache&quot; &quot;.&quot;;
        ///
        ///workspace -fr &quot;images&quot; &quot;.&quot;;
        ///
        ///workspace -fr &quot;offlineEdit&quot; &quot;.&quot;;
        ///
        ///workspace -fr &quot;furShadowMap&quot; &quot;.&quot;;
        ///
        ///workspace -fr &quot;iprImages&quot; &quot;.&quot;;
        ///
        ///workspace -fr &quot;renderData&quot; &quot;.&quot;;
        ///
        ///workspace -fr &quot;scripts&quot; &quot;.&quot;;
        ///
        ///workspace -fr &quot;fileCache&quot; &quot;.&quot;;
        ///
        ///workspace -fr &quot;eps&quot; &quot;.&quot;;
        ///
        ///workspace -fr &quot;shaders&quot; &quot;.&quot;;
        ///
        ///workspace -fr &quot;3dPaintTextures&quot; &quot;.&quot;;
        ///
        ///workspace -fr &quot;translatorData&quot; &quot;.&quot;;
        ///
        ///workspace -fr &quot;mel&quot; &quot;.&quot;;
        ///
        ///workspace -fr &quot;furFiles&quot; &quot;.&quot;;
        ///
        ///workspace -fr &quot;O [rest of string was truncated]&quot;;.
        /// </summary>
        internal static string workspace {
            get {
                return ResourceManager.GetString("workspace", resourceCulture);
            }
        }
    }
}
