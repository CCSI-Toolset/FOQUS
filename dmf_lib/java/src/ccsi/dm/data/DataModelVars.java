package ccsi.dm.data;

public class DataModelVars {
	/*
	 * Note: In Alfresco, all aspect types visible through CMIS are prefixed
	 * with "P:", document types are prefixed with "D:" and folder types are
	 * prefixed with "F:".
	 */
	public static final String P_PREFIX = "P:";
	public static final String D_PREFIX = "D:";
	public static final String F_PREFIX = "F:";

	// fields
	// Folder specific
	public static final String CCSI_FIXED_FORM = "ccsi:fixedForm";

	// File specific
	public static final String CCSI_EXT_LINK = "ccsi:link";
	public static final String CCSI_MIMETYPE = "ccsi:mimetype";
	public static final String CCSI_CHECKSUM = "ccsi:checksum";
	public static final String CCSI_CONFIDENCE = "ccsi:confidenceDegree";
	public static final String CCSI_VER_REQ = "ccsi:versionRequirements";
	public static final String CCSI_SIM = "ccsi:simulations";
	public static final String CCSI_PARENTS = "ccsi:parents";

	// Config specific
	public static final String CCSI_CONFIGFILE_TIMESTEP = "sbf_c:Timestep";
	public static final String CCSI_CONFIGFILE_RELATIVE_TOLERANCE = "sbf_c:RelativeTolerance";
	public static final String CCSI_CONFIGFILE_ABSOLUTE_TOLERANCE = "sbf_c:AbsoluteTolerance";
	public static final String CCSI_CONFIGFILE_SORBENT_DENSITY = "sbf_c:SorbentDensity";
	public static final String CCSI_CONFIGFILE_ATMOSPHERIC_PRESSURE = "sbf_c:AtmosphericPressure";
	public static final String CCSI_CONFIGFILE_DRY_LOW_REACTION_ENTHALPY = "sbf_c:DryReactionEnthalpyLow";
	public static final String CCSI_CONFIGFILE_DRY_HIGH_REACTION_ENTHALPY = "sbf_c:DryReactionEnthalpyHigh";
	public static final String CCSI_CONFIGFILE_DRY_LOW_REACTION_ENTROPY = "sbf_c:DryReactionEntropyLow";
	public static final String CCSI_CONFIGFILE_DRY_HIGH_REACTION_ENTROPY = "sbf_c:DryReactionEntropyHigh";
	public static final String CCSI_CONFIGFILE_DRY_LOW_ACTIVATION_ENTHALPY = "sbf_c:DryActivationEnthalpyLow";
	public static final String CCSI_CONFIGFILE_DRY_HIGH_ACTIVATION_ENTHALPY = "sbf_c:DryActivationEnthalpyHigh";
	public static final String CCSI_CONFIGFILE_DRY_LOW_PRESEXPONENTIAL_FACTOR = "sbf_c:DryPreexponentialFactorLow";
	public static final String CCSI_CONFIGFILE_DRY_HIGH_PRESEXPONENTIAL_FACTOR = "sbf_c:DryPreexponentialFactorHigh";
	public static final String CCSI_CONFIGFILE_WAT_LOW_NUMBER_ACTIVEADSORPSITES = "sbf_c:WatNumberActiveAdsorpSitesLow";
	public static final String CCSI_CONFIGFILE_WAT_HIGH_NUMBER_ACTIVEADSORPSITES = "sbf_c:WatNumberActiveAdsorpSitesHigh";
	public static final String CCSI_CONFIGFILE_WAT_LOW_REACTION_ENTHALPY = "sbf_c:WatReactionEnthalpyLow";
	public static final String CCSI_CONFIGFILE_WAT_HIGH_REACTION_ENTHALPY = "sbf_c:WatReactionEnthalpyHigh";
	public static final String CCSI_CONFIGFILE_WAT_LOW_REACTION_ENTROPY = "sbf_c:WatReactionEntropyLow";
	public static final String CCSI_CONFIGFILE_WAT_HIGH_REACTION_ENTROPY = "sbf_c:WatReactionEntropyHigh";
	public static final String CCSI_CONFIGFILE_WAT_LOW_ACTIVATION_ENTHALPY = "sbf_c:WatActivationEnthalpyLow";
	public static final String CCSI_CONFIGFILE_WAT_HIGH_ACTIVATION_ENTHALPY = "sbf_c:WatActivationEnthalpyHigh";
	public static final String CCSI_CONFIGFILE_WAT_LOW_PRESEXPONENTIAL_FACTOR = "sbf_c:WatPreexponentialFactorLow";
	public static final String CCSI_CONFIGFILE_WAT_HIGH_PRESEXPONENTIAL_FACTOR = "sbf_c:WatPreexponentialFactorHigh";
	public static final String CCSI_CONFIGFILE_HUMID_LOW_REACTION_ENTHALPY = "sbf_c:HumidReactionEnthalpyLow";
	public static final String CCSI_CONFIGFILE_HUMID_HIGH_REACTION_ENTHALPY = "sbf_c:HumidReactionEnthalpyHigh";
	public static final String CCSI_CONFIGFILE_HUMID_LOW_REACTION_ENTROPY = "sbf_c:HumidReactionEntropyLow";
	public static final String CCSI_CONFIGFILE_HUMID_HIGH_REACTION_ENTROPY = "sbf_c:HumidReactionEntropyHigh";
	public static final String CCSI_CONFIGFILE_HUMID_LOW_ACTIVATION_ENTHALPY = "sbf_c:HumidActivationEnthalpyLow";
	public static final String CCSI_CONFIGFILE_HUMID_HIGH_ACTIVATION_ENTHALPY = "sbf_c:HumidActivationEnthalpyHigh";
	public static final String CCSI_CONFIGFILE_HUMID_LOW_PRESEXPONENTIAL_FACTOR = "sbf_c:HumidPreexponentialFactorLow";
	public static final String CCSI_CONFIGFILE_HUMID_HIGH_PRESEXPONENTIAL_FACTOR = "sbf_c:HumidPreexponentialFactorHigh";
	public static final String CCSI_CONFIGFILE_NUMBER_PSO = "sbf_c:NumberOfPSO";

	// Data specific
	public static final String CCSI_DATAFILE_MIN_CO2 = "sbf_d:CO2PressureMin";
	public static final String CCSI_DATAFILE_MAX_CO2 = "sbf_d:CO2PressureMax";
	public static final String CCSI_DATAFILE_MIN_H2O = "sbf_d:H2OPressureMin";
	public static final String CCSI_DATAFILE_MAX_H2O = "sbf_d:H2OPressureMax";
	public static final String CCSI_DATAFILE_MIN_TEMP = "sbf_d:TemperatureMin";
	public static final String CCSI_DATAFILE_MAX_TEMP = "sbf_d:TemperatureMax";
	public static final String CCSI_DATAFILE_TIME_DURATION = "sbf_d:TimeDuration";
	public static final String CCSI_DATAFILE_TIME_STEP = "sbf_d:TimeStep";

	// Excel specific	
	public static final String CCSI_EXCELFILE_EXPERIMENTER_NAME = "sbf_e:ExperimenterName";
	public static final String CCSI_EXCELFILE_EXPERIMENT_DATE= "sbf_e:ExperimentDate";

	// Output specific
	public static final String CCSI_OUTPUTFILE_MIN_COST = "sbf_o:CostMin";
	public static final String CCSI_OUTPUTFILE_MAX_COST = "sbf_o:CostMax";
	public static final String CCSI_OUTPUTFILE_NUMBEROFITERATIONS = "sbf_o:NumberOfIterations";
	public static final String CCSI_OUTPUTFILE_NUMBEROFPARAMS = "sbf_o:NumberOfParams";
	public static final String CCSI_OUTPUTFILE_DH_KAP1 = "sbf_o:dh_kap1";
	public static final String CCSI_OUTPUTFILE_DS_KAP1 = "sbf_o:ds_kap1";
	public static final String CCSI_OUTPUTFILE_DH_K1 = "sbf_o:dh_k1";
	public static final String CCSI_OUTPUTFILE_ZETA_K1 = "sbf_o:zeta_k1";
	public static final String CCSI_OUTPUTFILE_DH_KAPH = "sbf_o:dh_kaph";
	public static final String CCSI_OUTPUTFILE_DS_KAPH = "sbf_o:ds_kaph";
	public static final String CCSI_OUTPUTFILE_DH_KH = "sbf_o:dh_kh";
	public static final String CCSI_OUTPUTFILE_ZETA_KH = "sbf_o:zeta_kh";
	public static final String CCSI_OUTPUTFILE_DH_HAP2 = "sbf_o:dh_kap2";
	public static final String CCSI_OUTPUTFILE_DS_KAP2 = "sbf_o:ds_kap2";
	public static final String CCSI_OUTPUTFILE_DH_K2 = "sbf_o:dh_k2";
	public static final String CCSI_OUTPUTFILE_ZETA_K2 = "sbf_o:zeta_k2";
	public static final String CCSI_OUTPUTFILE_NV = "sbf_o:nv";

	// Aspect fields
	public static final String CM_TITLE = "cm:title";
	public static final String CM_DESCRIPTION = "cm:description";
	public static final String CM_AUTHOR = "cm:author";
	public static final String CCSI_HOW_UPLOADED = "ccsi:howUploaded";
	public static final String CMIS_VERSION_LABEL = "cmis:versionLabel";

	// Aspects
	public static final String CM_TITLED = "cm:titled";
	public static final String CM_AUDITABLE = "cm:auditable";
	public static final String CM_LOCKOWNER = "cm:lockOwner";
	public static final String CCSI_UPLOAD_ORIGIN = "ccsi:uploadOrigin";
	public static final String CCSI_DOCUMENT_ASPECT = "ccsi:documentAspect";

	// Types
	public static final String CCSI_DOCUMENT_V = "ccsi:documentv"; // versioned
	public static final String CCSI_DOCUMENT = "ccsi:document";
	public static final String CCSI_RELATIONSHIP = "ccsi:relationship";
	public static final String CCSI_FOLDER = "ccsi:folder";

	// File Types
	public static final String CCSI_CONFIGFILE = "sbf_c:meta";
	public static final String CCSI_EXCELDATAFILE = "sbf_e:meta";
	public static final String CCSI_TEXTDATAFILE = "sbf_d:meta";
	public static final String CCSI_OUTPUTFILE = "sbf_o:meta";
}
