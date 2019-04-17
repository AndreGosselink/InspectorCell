# -*- coding: utf-8 -*-
"""POD from tiff spec and OME spec
"""

IFD_TAGS = {
    254: 'NewSubfileType',
    255: 'SubfileType',
    256: 'ImageWidth',
    257: 'ImageLength',
    258: 'BitsPerSample',
    259: 'Compression',
    262: 'PhotometricInterpretation',
    263: 'Threshholding',
    264: 'CellWidth',
    265: 'CellLength',
    266: 'FillOrder',
    269: 'DocumentName',
    270: 'ImageDescription',
    271: 'Make',
    272: 'Model',
    273: 'StripOffsets',
    274: 'Orientation',
    277: 'SamplesPerPixel',
    278: 'RowsPerStrip',
    279: 'StripByteCounts',
    280: 'MinSampleValue',
    281: 'MaxSampleValue',
    282: 'XResolution',
    283: 'YResolution',
    284: 'PlanarConfiguration',
    285: 'PageName',
    286: 'XPosition',
    287: 'YPosition',
    288: 'FreeOffsets',
    289: 'FreeByteCounts',
    290: 'GrayResponseUnit',
    291: 'GrayResponseCurve',
    292: 'T4Options',
    293: 'T6Options',
    296: 'ResolutionUnit',
    297: 'PageNumber',
    301: 'TransferFunction',
    305: 'Software',
    306: 'DateTime',
    315: 'Artist',
    316: 'HostComputer',
    317: 'Predictor',
    318: 'WhitePoint',
    319: 'PrimaryChromaticities',
    320: 'ColorMap',
    321: 'HalftoneHints',
    322: 'TileWidth',
    323: 'TileLength',
    324: 'TileOffsets',
    325: 'TileByteCounts',
    332: 'InkSet',
    333: 'InkNames',
    334: 'NumberOfInks',
    336: 'DotRange',
    337: 'TargetPrinter',
    338: 'ExtraSamples',
    339: 'SampleFormat',
    340: 'SMinSampleValue',
    341: 'SMaxSampleValue',
    342: 'TransferRange',
    512: 'JPEGProc',
    513: 'JPEGInterchangeFormat',
    514: 'JPEGInterchangeFormatLngth',
    515: 'JPEGRestartInterval',
    517: 'JPEGLosslessPredictors',
    518: 'JPEGPointTransforms',
    519: 'JPEGQTables',
    520: 'JPEGDCTables',
    521: 'JPEGACTables',
    529: 'YCbCrCoefficients',
    530: 'YCbCrSubSampling',
    531: 'YCbCrPositioning',
    532: 'ReferenceBlackWhite',
}

#           key: (char, desc)
IFD_TYPES = {
    1: ('B', 'BYTE'),
    2: ('B', 'ASCII'),
    3: ('H', 'SHORT'),
    4: ('I', 'LONG'),
    5: ('Q', 'RATIONAL'),
    6: ('b', 'SBYTE'),
    7: ('B', 'UNDEFINED'),
    8: ('h', 'SSHORT'),
    9: ('i', 'SLONG'),
    10: ('q', 'SRATIONAL'),
    11: ('f', 'FLOAT'),
    12: ('d', 'DOUBLE'),
}


OME_XML_TEMP = r"""<?xml version="1.0" encoding="UTF-8"?>
<!-- Warning: this comment is an OME-XML metadata block, which contains
crucial dimensional parameters and other important metadata. Please edi
t cautiously (if at all), and back up the original data before doing so
. For more information, see the OME-TIFF web site: https://docs.openmic
roscopy.org/latest/ome-model/ome-tiff/. -->                            
<OME xmlns="http://www.openmicroscopy.org/Schemas/OME/2016-06"         
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"             
     Creator="OME Bio-Formats 5.9.0"                                   
     UID="urn:uuid:dd04702c-4498-4e13-ae3a-b7b5c677abac"               
     xsi:schemaLocation="http://www.openmicroscopy.org/Schemas/OME/2016-06
     http://www.openmicroscopy.org/Schemas/OME/2016-06/ome.xsd">        
     <Image ID="Image:0" Name="test.ome.tiff">                         
        <Pixels BigEndian="false" DimensionOrder="XYCZT" ID="Pixels:0" 
                Interleaved="false" SizeC="1" SizeT="1" SizeX="462"    
                SizeY="462" SizeZ="1" Type="uint16">                   
            <Channel ID="Channel:0:0" SamplesPerPixel="1">             
                <LightPath/>                                           
            </Channel>                                                 
            <TiffData FirstC="0" FirstT="0" FirstZ="0" IFD="0"         
                PlaneCount="1">                                        
                <UUID FileName="test.ome.tiff">                        
                    urn:uuid:dd04702c-4498-4e13-ae3a-b7b5c677abac      
                </UUID>                                                
            </TiffData>                                                
        </Pixels>                                                      
    </Image>                                                           
    <StructuredAnnotations/>                                           
</OME>"""

OME_INFO = r'<?xml version="1.0" encoding="UTF-8"?>'
OME_COMMENT = r'<!-- Warning: this comment is an OME-XML metadata block' +\
', which contains crucial dimensional parameters and other important me' +\
'tadata. Please edit cautiously (if at all), and back up the original d' +\
'ata before doing so. For more information, see the OME-TIFF web site: ' +\
'https://docs.openmicroscopy.org/latest/ome-model/ome-tiff/. -->'

OME_ROOT = r'<OME xmlns="http://www.openmicroscopy.org/Schemas/OME/2016' +\
'-06" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaL' +\
'ocation="http://www.openmicroscopy.org/Schemas/OME/2016-06 http://www.' +\
'openmicroscopy.org/Schemas/OME/2016-06/ome.xsd"></OME>'


XML_PROCESSING = b'<?xml version="1.0" encoding="UTF-8"?>'
