#!/usr/bin/env python
# D. Jones - 1/7/16
#./ovdataIIP.py ps1phot_prob_onlyhostz.fitres ps1_smallsim_newiasig08.fitres MURES:MURES:MURES:MURES:MURES:MURES:MURES:MURES:MURES:MURES:MURES --clobber -o defaultwcuts.pdf --dataM -19.23 --cutwin FITPROB 0.01 1.0 --ylog --defaultcuts

class txtobj:
    def __init__(self,filename):

        fin = open(filename,'r')
        lines = fin.readlines()
        for l in lines:
            if l.startswith('VARNAMES:'):
                l = l.replace('\n','')
                coldefs = l.split()
                break
                
        with open(filename) as f:
            reader = [x.split() for x in f if x.startswith('SN:')]

        i = 0
        for column in zip(*reader):
            try:
                self.__dict__[coldefs[i]] = np.array(column[:]).astype(float)
            except:
                self.__dict__[coldefs[i]] = np.array(column[:])
            i += 1

class ovhist:
    def __init__(self):
        self.clobber = False
        self.verbose = False

    def add_options(self, parser=None, usage=None, config=None):
        import optparse
        if parser == None:
            parser = optparse.OptionParser(usage=usage, conflict_handler="resolve")

        # The basics
        parser.add_option('-v', '--verbose', action="count", dest="verbose",default=1)
        parser.add_option('--clobber', default=False, action="store_true",
                          help='overwrite output file if it exists')
        parser.add_option('--cutwin',default=[],
                          type='string',action='append',
                          help='parameter range for specified variable',nargs=3)
        parser.add_option('--defaultcuts',default=False,action='store_true',
                          help='make the default sample cuts')
        parser.add_option('--x1cellipse',default=False,action='store_true',
                          help='elliptical default cut, not box; use in conjunction w/ defaultcuts')
        parser.add_option('--alpha',type='float',default=0.147,
                          help='SALT2 alpha for computing distances (default=%default)')
        parser.add_option('--beta',type='float',default=3.13,
                          help='SALT2 beta (default=%default)')
        parser.add_option('--dataM',type='float',default=-19.3,
                          help='SALT2 M parameter for data only (default=%default)')
        parser.add_option('--simM',type='float',default=-19.3,
                          help='SALT2 M parameter for simulations only (default=%default)')
        parser.add_option('--sigint',type='float',default=0.115,
                          help='Intrinsic Dispersion for computing distance errors (default=%default)')

        parser.add_option('-o','--outfile',type='string',default='',
                          help='output figure file (default=ovplot_[varname].pdf)')
        parser.add_option('--interact', default=False, action="store_true",
                          help='open up the figure interactively')
        parser.add_option('--nbins',type='int',default=40,
                          help='number of histogram bins (default=%default)')
        parser.add_option('--bins',type='float',default=(None,None,None),
                          help="""3 arguments specifying number of bins and the min. and max. of the histogram range.  
                          For multi-plot mode, use the --cutwin options instead.""",nargs=3)
        parser.add_option('--ylog', default=False, action="store_true",
                          help='log-scaled y-axis')
        parser.add_option('--ylim', default=(None,None), type='float',
                          help='custom y-axis limits',nargs=2)
        parser.add_option('--journal', default=False, action="store_true",
                          help='make journal figure')
        parser.add_option('--non1aindex', default=False, action="store_true",
                          help='plots of non1a index')
        
        return(parser)

    def main(self,datafile,simfile):
        data = txtobj(datafile)
        sim = txtobj(simfile)

        sim_non1a_list = [201,204,208,210,213,214,215,
                          216,219,220,221,222,223,224,
                          225,226,227,228,229,230,231,
                          232,233,235,206,209,2,103,104,
                          105,202,203,2121,234,21,22,101,
                          102,205,207,211,217,218,300]
        sim_type_list = [20,21,22,23,32,33,41,42,43]
        
        # getting distance modulus is slow, so don't do it unless necessary
        getMU = False
        if len(self.options.cutwin):
            for cutopt in self.options.cutwin:
                if 'MU' in cutopt[0]: getMU = True
        for h in self.options.histvar:
            if 'MU' in h: getMU = True
                
        if 'MU' in self.options.histvar or getMU:
            if not data.__dict__.has_key('MU'):
                data.MU,data.MUERR = salt2mu(x1=data.x1,x1err=data.x1ERR,c=data.c,cerr=data.cERR,mb=data.mB,mberr=data.mBERR,
                                             cov_x1_c=data.COV_x1_c,cov_x1_x0=data.COV_x1_x0,cov_c_x0=data.COV_c_x0,
                                             alpha=self.options.alpha,beta=self.options.beta,
                                             x0=data.x0,sigint=self.options.sigint,z=data.zHD,M=self.options.dataM)
                from astropy.cosmology import Planck13 as cosmo
                if not data.__dict__.has_key('MURES'):
                    data.MURES = data.MU - cosmo.distmod(data.zHD).value
            if not sim.__dict__.has_key('MU'):
                sim.MU,sim.MUERR = salt2mu(x1=sim.x1,x1err=sim.x1ERR,c=sim.c,cerr=sim.cERR,mb=sim.mB,mberr=sim.mBERR,
                                           cov_x1_c=sim.COV_x1_c,cov_x1_x0=sim.COV_x1_x0,cov_c_x0=sim.COV_c_x0,
                                           alpha=self.options.alpha,beta=self.options.beta,
                                           x0=sim.x0,sigint=self.options.sigint,z=sim.zHD,M=self.options.simM)
                from astropy.cosmology import Planck13 as cosmo
                if not sim.__dict__.has_key('MURES'):
                    sim.MURES = sim.MU - cosmo.distmod(sim.zHD).value

#        sim.SIM_TYPE_INDEX[sim.SIM_NONIA_INDEX == 103] = -99
#        sim.SIM_TYPE_INDEX[sim.SIM_NONIA_INDEX == 104] = -99
#        sim.SIM_TYPE_INDEX[sim.SIM_NONIA_INDEX == 105] = -99
        
        sim = self.mkcuts(sim,fitresfile=simfile)
        data.SIM_TYPE_INDEX[:] = 32
        data = self.mkcuts(data,fitresfile=datafile)
        import pdb; pdb.set_trace()
        if self.options.journal:
            plt.rcParams['figure.figsize'] = (6,6)
        else:
            plt.rcParams['figure.figsize'] = (8.5,11)
            from matplotlib.backends.backend_pdf import PdfPages
            if not self.options.outfile:
                self.options.outfile = 'ovplot_%s.pdf'%("_".join(self.options.histvar))
            if not os.path.exists(self.options.outfile) or self.options.clobber:
                pdf_pages = PdfPages(self.options.outfile)
            else:
                print('File %s exists!  Not clobbering...'%self.options.outfile)
        totalcount = 0                
        for histvar,i in zip(self.options.histvar,
                             np.arange(len(self.options.histvar))+1):
            if self.options.journal:
                plt.clf()
                ax = plt.subplot(1,1,1)
            else:
                if i%3 == 1: fig = plt.figure()
                if i == 3: subnum = 3
                else: subnum = i%3
                ax = plt.subplot(3,1,subnum)
            ax.set_xlabel(histvar,labelpad=0)
            ax.set_ylabel('#')
#            ax.set_ylim([0,40])
            
            self.options.histmin,self.options.histmax = None,None
            if len(self.options.cutwin):
                for cutopt in self.options.cutwin:
                    var,min,max = cutopt[0],cutopt[1],cutopt[2]; min,max = float(min),float(max)
                if var == histvar:
                    self.options.histmin = min; self.options.histmax = max
            if not self.options.histmin:
                self.options.histmin = np.min(np.append(sim.__dict__[histvar],data.__dict__[histvar]))
                self.options.histmax = np.max(np.append(sim.__dict__[histvar],data.__dict__[histvar]))


            cols_CC = np.where((sim.SIM_TYPE_INDEX != 1) & 
                               (sim.__dict__[histvar] >= self.options.histmin) &
                               (sim.__dict__[histvar] <= self.options.histmax))[0]
            cols_Ia = np.where((sim.SIM_TYPE_INDEX == 1) & 
                               (sim.__dict__[histvar] >= self.options.histmin) &
                               (sim.__dict__[histvar] <= self.options.histmax))[0]

            # bins command options
            if self.options.bins[0]: self.options.nbins = self.options.bins[0]
            if self.options.bins[1]: self.options.histmin = self.options.bins[1]
            if self.options.bins[2]: self.options.histmax = self.options.bins[2]

            histint = (self.options.histmax - self.options.histmin)/self.options.nbins
            histlen = float(len(np.where((data.__dict__[histvar] > self.options.histmin) &
                                         (data.__dict__[histvar] < self.options.histmax))[0]))
            n_nz = np.histogram(data.__dict__[histvar],bins=np.arange(self.options.histmin,self.options.histmax,histint))
            import scipy.stats
            errl,erru = scipy.stats.poisson.interval(0.68,n_nz[0])
            ax.plot(n_nz[1][:-1]+(n_nz[1][1]-n_nz[1][0])/2.,n_nz[0],'o',color='k',lw=2,label='data')
            ax.errorbar(n_nz[1][:-1]+(n_nz[1][1]-n_nz[1][0])/2.,n_nz[0],yerr=[n_nz[0]-errl,erru-n_nz[0]],color='k',fmt=' ',lw=2)

            # single out the SNe Ia, Ibc, II
            n_nz = np.histogram(data.__dict__[histvar][data.PBAYES_Ia > 0.95],bins=np.arange(self.options.histmin,self.options.histmax,histint))
            errl,erru = scipy.stats.poisson.interval(0.68,n_nz[0])
            ax.plot(n_nz[1][:-1]+(n_nz[1][1]-n_nz[1][0])/2.,n_nz[0],'o',color='r',lw=2,label='P(Ia) > 0.95')
            ax.errorbar(n_nz[1][:-1]+(n_nz[1][1]-n_nz[1][0])/2.,n_nz[0],yerr=[n_nz[0]-errl,erru-n_nz[0]],color='k',fmt=' ',lw=2)

            n_nz = np.histogram(data.__dict__[histvar][data.PBAYES_Ibc > 0.95],bins=np.arange(self.options.histmin,self.options.histmax,histint))
            errl,erru = scipy.stats.poisson.interval(0.68,n_nz[0])
            ax.plot(n_nz[1][:-1]+(n_nz[1][1]-n_nz[1][0])/2.,n_nz[0],'o',color='b',lw=2,label='P(Ibc) > 0.95')
            ax.errorbar(n_nz[1][:-1]+(n_nz[1][1]-n_nz[1][0])/2.,n_nz[0],yerr=[n_nz[0]-errl,erru-n_nz[0]],color='k',fmt=' ',lw=2)

            n_nz = np.histogram(data.__dict__[histvar][data.PBAYES_II > 0.95],bins=np.arange(self.options.histmin,self.options.histmax,histint))
            errl,erru = scipy.stats.poisson.interval(0.68,n_nz[0])
            ax.plot(n_nz[1][:-1]+(n_nz[1][1]-n_nz[1][0])/2.,n_nz[0],'o',color='g',lw=2,label='P(II) > 0.95')
            ax.errorbar(n_nz[1][:-1]+(n_nz[1][1]-n_nz[1][0])/2.,n_nz[0],yerr=[n_nz[0]-errl,erru-n_nz[0]],color='k',fmt=' ',lw=2)

            
            n_nz = np.histogram(sim.__dict__[histvar],bins=np.arange(self.options.histmin,self.options.histmax,histint))
            ax.plot(n_nz[1][:-1],n_nz[0]/float(len(cols_Ia)+len(cols_CC))*histlen,
                    color='k',drawstyle='steps-post',lw=2,label='All Sim. SNe',ls='-.')
            if self.options.non1aindex:
                for sim_non1a,color in zip(sim_non1a_list[4*(i-1):4*i],['b','g','purple','darkorange']):
                    n_nz = np.histogram(sim.__dict__[histvar][cols_CC][np.where(sim.SIM_NONIA_INDEX[cols_CC] == sim_non1a)],
                                        bins=np.arange(self.options.histmin,self.options.histmax,histint))
                    ax.plot(n_nz[1][:-1],n_nz[0]/float(len(cols_Ia)+len(cols_CC))*histlen,
                            drawstyle='steps-post',lw=2,label=sim_non1a,color=color)
            else:
                for sim_non1a,color in zip(sim_type_list[5*(i-1):5*i],['b','g','purple','darkorange','teal']):
                    n_nz = np.histogram(sim.__dict__[histvar][cols_CC][np.where(sim.SIM_TYPE_INDEX[cols_CC] == sim_non1a)],
                                        bins=np.arange(self.options.histmin,self.options.histmax,histint))
                    ax.plot(n_nz[1][:-1],n_nz[0]/float(len(cols_Ia)+len(cols_CC))*histlen,
                            drawstyle='steps-post',lw=2,label=sim_non1a,color=color)

                #                    totalcount += len(np.where(sim.SIM_NONIA_INDEX[cols_CC] == sim_non1a)[0])
#                    print sim_non1a,len(np.where(sim.SIM_NONIA_INDEX[cols_CC] == sim_non1a)[0]),totalcount
#            import pdb; pdb.set_trace()
            n_nz = np.histogram(sim.__dict__[histvar][cols_Ia],bins=np.arange(self.options.histmin,self.options.histmax,histint))
            ax.plot(n_nz[1][:-1],n_nz[0]/float(len(cols_Ia)+len(cols_CC))*histlen,
                    color='r',drawstyle='steps-post',lw=2,label='Sim. SNe Ia')
            if self.options.ylim[1]: ax.set_ylim([self.options.ylim[0],self.options.ylim[1]])
            if self.options.ylog:
                ax.set_yscale('log')
                if not self.options.ylim[0]: ax.set_ylim(bottom=0.01)

            print('Variable: %s'%histvar)
            print('NDATA: %i'%len(data.CID))
            print('MC Scale: %.1f'%(histlen/float(len(cols_Ia)+len(cols_CC))))
            if len(cols_Ia):
                print('N(CC Sim.)/N(Ia Sim.): %.3f'%(len(cols_CC)/float(len(cols_Ia))))
            else:
                print('N(CC Sim.)/N(Ia Sim.): inf')

            ax.legend(loc='upper right',numpoints=1,prop={'size':10},fancybox=True)

            if self.options.journal or i%3 == 1:
                box = ax.get_position()
                ax.set_position([box.x0, box.y0,# + box.height * 0.15,
                                 box.width, box.height * 0.85])
                # Put a legend below current axis
                #if self.options.journal:
                #    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.2),
                #              fancybox=True, ncol=2,numpoints=1)
                #else:
                #    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.6),
                #              fancybox=True, ncol=2,numpoints=1)
                    
            if self.options.interact:
                plt.show()
            
            if not self.options.journal:
                if i%3 == 1: self.plottitle(ax)
                if not i%3:
                    if not os.path.exists(self.options.outfile) or self.options.clobber:
                        pdf_pages.savefig(fig)
            else:
                if not self.options.outfile:
                    outfile = 'ovplot_%s.png'%histvar
                else: outfile = self.options.outfile
                if not os.path.exists(outfile) or self.options.clobber:
                    plt.savefig(outfile)
                else:
                    print('File %s exists!  Not clobbering...'%outfile)
#            if histvar == 'MURES': import pdb; pdb.set_trace()
        if not self.options.journal:
            if not os.path.exists(self.options.outfile) or self.options.clobber:
                if i%3:
                    pdf_pages.savefig(fig)
                pdf_pages.close()
                
    def plottitle(self,ax):
        from textwrap import wrap
        import datetime; dt = datetime.date.today()
        titlestr = 'Created %i/%i/%i;  '%(dt.month,dt.day,dt.year)
        if self.options.defaultcuts:
            if self.options.x1cellipse:
                titlestr += '0.3 < c < 0.3; 3.0 < x1 < 3.0; pkMJDERR < 2/(1+z); x1ERR < 1; FITPROB > 0.001; '
            else:
                titlestr += 'c/0.3^2 + x1/3.0^2 < 1; pkMJDERR < 2/(1+z); x1ERR < 1; FITPROB > 0.001; '
        if len(self.options.cutwin):
            for cutopt in self.options.cutwin:
                i,min,max = cutopt[0],cutopt[1],cutopt[2]; min,max = float(min),float(max)
                titlestr += '%s < %s < %s; '%(cutopt[1],cutopt[0],cutopt[2])
        ax.set_title("\n".join(wrap(titlestr[:-2],width=60)),fontsize=12)
        
    def mkcuts(self,fr,fitresfile=None):
        # uncertainties
        sf = -2.5/(fr.x0*np.log(10.0))
        cov_mb_c = fr.COV_c_x0*sf
        cov_mb_x1 = fr.COV_x1_x0*sf
    
        invvars = 1.0 / (fr.mBERR**2.+ self.options.alpha**2. * fr.x1ERR**2. + self.options.beta**2. * fr.cERR**2. + \
                             2.0 * self.options.alpha * (fr.COV_x1_x0*sf) - 2.0 * self.options.beta * (fr.COV_c_x0*sf) - \
                             2.0 * self.options.alpha*self.options.beta * (fr.COV_x1_c) )
        if self.options.defaultcuts:
            if self.options.x1cellipse:
                # I'm just going to assume cmax = abs(cmin) and same for x1
                cols = np.where((fr.x1**2./3.0**2. + fr.c**2./0.3**2. < 1) &
                                (fr.x1ERR < 1) & (fr.PKMJDERR < 2*(1+fr.zHD)) &
                                (fr.FITPROB >= 0.001) & (invvars > 0))
            else:
                cols = np.where((fr.x1 > -3.0) & (fr.x1 < 3.0) &
                                (fr.c > -0.3) & (fr.c < 0.3) &
                                (fr.x1ERR < 1) & (fr.PKMJDERR < 2*(1+fr.zHD)) &
                                (fr.FITPROB >= 0.001) & (invvars > 0))

            for k in fr.__dict__.keys():
                fr.__dict__[k] = fr.__dict__[k][cols]
                    
        if len(self.options.cutwin):
            cols = np.arange(len(fr.CID))
            for cutopt in self.options.cutwin:
                i,min,max = cutopt[0],cutopt[1],cutopt[2]; min,max = float(min),float(max)
                if not fr.__dict__.has_key(i):
                    if i not in self.options.histvar:
                        print('Warning : key %s not in fitres file %s! Ignoring for this file...'%(i,fitresfile))
                    else:
                        raise exceptions.RuntimeError('Error : key %s not in fitres file %s!'%(i,fitresfile))
                else:
                    cols = cols[np.where((fr.__dict__[i][cols] >= min) & (fr.__dict__[i][cols] <= max))]

            for k in fr.__dict__.keys():
                fr.__dict__[k] = fr.__dict__[k][cols]
            
        return(fr)

def salt2mu(x1=None,x1err=None,
            c=None,cerr=None,
            mb=None,mberr=None,
            cov_x1_c=None,cov_x1_x0=None,cov_c_x0=None,
            alpha=None,beta=None,
            alphaerr=None,betaerr=None,
            M=19.3,x0=None,sigint=None,
            z=None,peczerr=0.0005):
    import numpy as np
    sf = -2.5/(x0*np.log(10.0))
    cov_mb_c = cov_c_x0*sf
    cov_mb_x1 = cov_x1_x0*sf
    mu_out = mb + x1*alpha - beta*c - M
    invvars = 1.0 / (mberr**2.+ alpha**2. * x1err**2. + beta**2. * cerr**2. + \
                         2.0 * alpha * (cov_x1_x0*sf) - 2.0 * beta * (cov_c_x0*sf) - \
                         2.0 * alpha*beta * (cov_x1_c) )
        
    zerr = peczerr*5.0/np.log(10)*(1.0+z)/(z*(1.0+z/2.0))
    muerr_out = np.sqrt(1/invvars + zerr**2. + 0.055**2.*z**2.)
    if sigint: muerr_out = np.sqrt(muerr_out**2. + sigint**2.)
    return(mu_out,muerr_out)
        
if __name__ == "__main__":
    usagestring="""
ovdatamc.py <DataFitresFile> <SimFitresFile>  <varName1:varName2:varName3....>  [--cutwin NN_ITYPE 1 1 --cutwin x1 -3 3]

Given a FITRES file for both data and an SNANA simulation, 
ovdatamc.py creates histograms that compare fit parameters or other 
variables between the two.  If distance moduli/residuals are not 
included in the fitres file, specify MU/MURES as the varName and 
they will be computed with standard SALT2 nuisance parameters.  To 
specify multiple variable names, use colons to separate them.

use -h/--help for full options list
"""

    import exceptions
    import os
    import optparse

    hist = ovhist()

    # read in the options from the param file and the command line
    # some convoluted syntax here, making it so param file is not required
    parser = hist.add_options(usage=usagestring)
    options,  args = parser.parse_args()

    try:
        datafile,simfile,histvar = args[0],args[1],args[2]
    except:
        import sys
        print(usagestring)
        print('Error : incorrect or wrong number of arguments')
        sys.exit(1)
        
    import numpy as np
    import pylab as plt

    hist.options = options
    hist.verbose = options.verbose
    hist.clobber = options.clobber
    hist.options.histvar = histvar.split(':')

    hist.main(datafile,simfile)
